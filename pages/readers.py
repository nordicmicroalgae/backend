import os
import pathlib
import re

import yaml


class MarkdownReader:
    metadata_delimiter_re = re.compile(r"^-{3,}\s*$", re.MULTILINE)

    def __init__(self, source_directory):
        self._source_directory = pathlib.Path(source_directory)

    def read_document(self, document_name):
        document_name = os.path.basename(document_name)
        document_path = pathlib.Path(self._source_directory, document_name).with_suffix(
            ".md"
        )

        content = ""
        metadata = {}

        with open(document_path, "r") as in_file:
            content = in_file.read()

            if self.metadata_delimiter_re.match(content):
                _, metadata, content = self.metadata_delimiter_re.split(content, 2)

                content = content.strip()

                metadata = metadata.strip()
                metadata = yaml.safe_load(metadata)

        return (content, metadata)

    @property
    def documents(self):
        document_names = []
        for file_path in self._source_directory.glob("*.md"):
            document_names.append(file_path.stem)
        return document_names
