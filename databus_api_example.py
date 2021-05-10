import requests
import json
import hashlib
import sys
from datetime import datetime
from dataclasses import dataclass, field
from typing import List


@dataclass
class DataGroup:
    account_name: str
    id: str
    label: str
    title: str
    comment: str
    abstract: str
    description: str
    context: str = "https://raw.githubusercontent.com/dbpedia/databus-git-mockup/main/dev/context.jsonld"

    def get_target_uri(self) -> str:

        return f"https://databus.dbpedia.org/{self.account_name}/{self.id}"

    def to_jsonld(self) -> str:
        """Generates the json representation of group documentation"""

        group_uri = f"https://databus.dbpedia.org/{self.account_name}/{self.id}"

        group_data_dict = {
            "@context": self.context,
            "@graph": [
                {
                    "@id": group_uri,
                    "@type": "Group",
                    "label": {"@value": self.label, "@language": "en"},
                    "title": {"@value": self.title, "@language": "en"},
                    "comment": {"@value": self.comment, "@language": "en"},
                    "abstract": {"@value": self.abstract, "@language": "en"},
                    "description": {"@value": self.description, "@language": "en"},
                }
            ],
        }
        return json.dumps(group_data_dict)


class DatabusFile:
    def __init__(self, uri: str, cvs: dict, file_ext: str, **kwargs):
        """Fetches the necessary information of a file URI for the deploy to the databus."""
        self.uri = uri
        self.cvs = cvs
        resp = requests.get(uri, **kwargs)
        if resp.status_code > 400:
            print(f"ERROR for {uri} -> Status {str(resp.status_code)}")

        self.sha256sum = hashlib.sha256(bytes(resp.content)).hexdigest()
        self.content_length = str(len(resp.content))
        self.file_ext = file_ext
        self.id_string = "_".join([f"{k}={v}" for k, v in cvs.items()]) + "." + file_ext


@dataclass
class DataVersion:
    account_name: str
    group: str
    artifact: str
    version: str
    title: str
    label: str
    publisher: str
    comment: str
    abstract: str
    description: str
    license: str
    databus_files: List[DatabusFile]
    issued: datetime = field(default_factory=datetime.now)
    context: str = "https://raw.githubusercontent.com/dbpedia/databus-git-mockup/main/dev/context.jsonld"

    def get_target_uri(self):

        return f"https://databus.dbpedia.org/{self.account_name}/{self.group}/{self.artifact}/{self.version}"

    def __distinct_cvs(self) -> dict:

        distinct_cv_definitions = {}
        for dbfile in self.databus_files:
            for key, value in dbfile.cvs.items():

                if key not in distinct_cv_definitions:
                    distinct_cv_definitions[key] = {
                        "@type": "rdf:Property",
                        "@id": f"dataid-cv:{key}",
                        "rdfs:subPropertyOf": {"@id": "dataid:contentVariant"},
                    }
        return distinct_cv_definitions

    def __dbfiles_to_dict(self):

        for dbfile in self.databus_files:
            file_dst = {
                "@id": self.version_uri + "#" + dbfile.id_string,
                "file": self.version_uri + "/" + self.artifact + "_" + dbfile.id_string,
                "@type": "dataid:SingleFile",
                "formatExtension": dbfile.file_ext,
                "compression": "none",
                "downloadURL": dbfile.uri,
                "byteSize": dbfile.content_length,
                "sha256sum": dbfile.sha256sum,
                "hasVersion": self.version,
            }
            for key, value in dbfile.cvs.items():

                file_dst[f"dataid-cv:{key}"] = value

            yield file_dst

    def to_jsonld(self) -> str:
        self.version_uri = (
            f"https://databus.dbpedia.org/{account_name}/{group}/{artifact}/{version}"
        )
        self.data_id_uri = self.version_uri + "#Dataset"

        self.artifact_uri = (
            f"https://databus.dbpedia.org/{account_name}/{group}/{artifact}"
        )

        self.group_uri = f"https://databus.dbpedia.org/{account_name}/{group}"

        self.timestamp = self.issued.strftime("%Y-%m-%dT%H:%M:%SZ")

        data_id_dict = {
            "@context": self.context,
            "@graph": [
                {
                    "@type": "dataid:Dataset",
                    "@id": self.data_id_uri,
                    "version": self.version_uri,
                    "artifact": self.artifact_uri,
                    "group": self.group_uri,
                    "hasVersion": self.version,
                    "issued": self.timestamp,
                    "publisher": self.publisher,
                    "label": {"@value": self.label, "@language": "en"},
                    "title": {"@value": self.title, "@language": "en"},
                    "comment": {"@value": self.comment, "@language": "en"},
                    "abstract": {"@value": self.abstract, "@language": "en"},
                    "description": {"@value": self.description, "@language": "en"},
                    "license": {"@id": self.license},
                    "distribution": [d for d in self.__dbfiles_to_dict()],
                }
            ],
        }

        for _, named_cv_prop in self.__distinct_cvs().items():
            data_id_dict["@graph"].append(named_cv_prop)

        return json.dumps(data_id_dict)


def deploy_to_databus(user: str, passwd: str, *databus_objects):
    try:
        data = {
            "client_id": "upload-api",
            "username": user,
            "password": passwd,
            "grant_type": "password",
        }

        print("Accessing new token...")
        token_response = requests.post(
            "https://databus.dbpedia.org/auth/realms/databus/protocol/openid-connect/token",
            data=data,
        )
        print(f"Response: Status {token_response.status_code}; Text: {token_response.text}")

        token = token_response.json()["access_token"]

    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)

    for dbobj in databus_objects:

        headers = {"Authorization": "Bearer " + token}

        print(f"Deploying {dbobj.get_target_uri()}")
        response = requests.put(
            dbobj.get_target_uri(), headers=headers, data=dbobj.to_jsonld()
        )
        print(f"Response: Status {response.status_code}; Text: {response.text}")


if __name__ == "__main__":

    # account for publishing the dataset, password required
    account_name = "denis"

    group = "lod-geoss-example"

    artifact = "api-example"

    version = "2021-05-10"

    title = "API example"

    publisher = "https://yum-yab.github.io/webid.ttl#this"

    label = "API example"

    comment = "This is a short comment about the test."

    abstract = "This a short abstract for the dataset. Since this is only a test it is quite insignificant."

    description = "A bit longer description of the dataset."

    license = "http://creativecommons.org/licenses/by/4.0/"

    files = [
        DatabusFile(
            "https://openenergy-platform.org/api/v0/schema/supply/tables/wind_turbine_library/rows/",
            {"type": "turbineData"},
            "json",
        ),
    ]

    databus_version = DataVersion(
        account_name=account_name,
        group=group,
        artifact=artifact,
        version=version,
        title=title,
        publisher=publisher,
        label=label,
        comment=comment,
        abstract=abstract,
        description=description,
        license=license,
        databus_files=files,
    )

    databus_group = DataGroup(
        account_name=account_name,
        id=group,
        label="LOD GEOSS Example",
        title="LOD GEOSS Example",
        abstract="Lorem ipsum dolor sit amet, consetetur sadipscing elitr.",
        comment="Lorem ipsum dolor sit amet, consetetur sadipscing elitr.",
        description="Lorem ipsum dolor sit amet, consetetur sadipscing elitr.",
    )

    deploy_to_databus(
        account_name, "passwort", databus_group, databus_version
    )
