import os
import time
from os import walk, makedirs
from os.path import isdir, isfile, join, exists, getmtime

import requests
from click import command, argument, option


class OCRPoller:
    LANG = "en"

    def __init__(self, src, dst, endpoint, key):
        self.src = src
        self.dst = dst
        self.headers = {'Ocp-Apim-Subscription-Key': key,
                        "Content-Type": "application/octet-stream"}
        self.url = endpoint + "/vision/v3.0-preview/read/analyze"

    def poll_changes(self, cycle=60):
        while True:
            if not isdir(self.src):
                raise ValueError("No such file or directory: %s" % self.src)
            if isfile(self.dst):
                raise ValueError("%s already exists and is a file.")
            if not exists(self.dst):
                makedirs(self.dst)
            self.ocr_sync()
            time.sleep(cycle)

    def ocr_sync(self):
        # Set the langauge that you want to recognize. The value can be "en" for English, and "es" for Spanish
        for filename, fp in walkfolder(self.src):
            dstfile = join(self.dst, filename) + ".txt"
            if exists(dstfile) and (isdir(dstfile) or getmtime(dstfile) >= getmtime(fp)):
                continue
            text = self.convert(fp)
            with open(dstfile, 'wt') as f:
                f.write(text)
            print("Converted %s to %s" % (fp, dstfile))

    def convert(self, filename):
        # Set image_url to the URL of an image that you want to recognize.
        # image_url = "https://upload.wikimedia.org/wikipedia/commons/d/dd/Cursive_Writing_on_Notebook_paper.jpg"
        data = open(filename, "rb").read()
        response = requests.post(
            self.url, headers=self.headers, data=data, params={'language': self.LANG})
        response.raise_for_status()

        # Extracting text requires two API calls: One call to submit the
        # image for processing, the other to retrieve the text found in the image.

        # Holds the URI used to retrieve the recognized text.
        operation_url = response.headers["Operation-Location"]

        # The recognized text isn't immediately available, so poll to wait for completion.
        analysis = {}
        poll = True
        while (poll):
            response_final = requests.get(
                operation_url, headers=self.headers)
            analysis = response_final.json()
            time.sleep(1)
            if ("analyzeResult" in analysis):
                poll = False
            if ("status" in analysis and analysis['status'] == 'failed'):
                poll = False
        if analysis['status'] == 'failed':
            return "Conversion failed"
        text = ""
        for page in analysis["analyzeResult"]["readResults"]:
            for line in page["lines"]:
                if all([word['confidence'] >= 1 for word in line['words']]):
                    text += "%s\n" % line["text"]
        return text


@command()
@argument('src')
@argument('dst')
@option('--cycle', '-c', type=int, default=60)
def run(src, dst, cycle):
    # Add your Computer Vision subscription key and endpoint to your environment variables.
    if 'COMPUTER_VISION_ENDPOINT' in os.environ:
        ENDPOINT = os.environ['COMPUTER_VISION_ENDPOINT']
    else:
        raise EnvironmentError("Missing environment variable $COMPUTER_VISION_ENDPOINT")

    if 'COMPUTER_VISION_SUBSCRIPTION_KEY' in os.environ:
        KEY = os.environ['COMPUTER_VISION_SUBSCRIPTION_KEY']
    else:
        raise EnvironmentError("Missing environment variable $COMPUTER_VISION_SUBSCRIPTION_KEY")
    ocr_poller = OCRPoller(src, dst, ENDPOINT, KEY)
    ocr_poller.poll_changes(cycle)


def walkfolder(dir):
    for dirpath, dirnames, filenames in walk(dir):
        for filename in filenames:
            if filename.endswith(".pdf"):
                yield filename, join(dirpath, filename)


if __name__ == "__main__":
    run()
