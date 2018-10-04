import requests
from bs4 import BeautifulSoup, element
import json
import re
import os
import datetime
from tqdm import tqdm

SOURCE_URL = 'https://www.elwis.de/DE/Sportschifffahrt/Sportbootfuehrerscheine/Fragenkatalog-Binnen/Fragenkatalog-Binnen-node.html'
IMAGE_REGEX = re.compile(r'(.*);jsessionid=.*') # Images have sessionID, this needs to be removed
ASSET_DIR = 'assets'
OUTPUT_JSON = 'output.json'

def logLine(message):
    printMessage = '\033[32m[\033[34m' + datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S') + '\033[32m]\033[0m'

    printMessage = printMessage + ' - ' + str(message)

    print(printMessage)

def downloadFile(url, destdir):
    if not os.path.exists(destdir):
        os.makedirs(destdir)

    localFilename = os.path.join(destdir, url.split('/')[-1])

    r = requests.get(url, stream=True)
    with open(localFilename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
    return localFilename

logLine('Retrieving main Page (' + SOURCE_URL + ')')
response = requests.get(SOURCE_URL)
questionsObject = []

if response.status_code == requests.codes.ok:
    parser = BeautifulSoup(response.text, 'html.parser')
    baseURL = parser.find('base')['href']
    for link in parser.select('#content a.RichTextIntLink.NavNode'):
        # print(link['href'])
        subpageURL = baseURL + link['href']
        questionsResponse = requests.get(subpageURL)
        logLine('Retrieving SubPage (' + subpageURL + ')')
        if questionsResponse.status_code == requests.codes.ok:
            questionsParser = BeautifulSoup(questionsResponse.text, 'html.parser')
            logLine('Parsing Questions')
            for questions in tqdm(questionsParser.select('#content > ol')):
                curQuestion = {}
                questionStr = ''
                for item in questions.find('li').children:
                    # We need to stop before answer list
                    if item.name == 'ol':
                        break

                    if type(item) == element.Tag:

                        # One Child, means we have text
                        if len(item.contents) == 1:
                            questionStr = questionStr + item.contents[0]
                        else:
                            # This means that we probably have an image
                            image = item.find('img')
                            if image:
                                imageSrc = IMAGE_REGEX.search(image['src'])
                                if imageSrc.groups:
                                    imageSrc = imageSrc.group(1)
                                else:
                                    imageSrc = image['src']

                                imageSrc = downloadFile(baseURL + imageSrc, ASSET_DIR)
                                questionStr = questionStr + '<img src="' + imageSrc + '" />'
                        continue

                    questionStr = questionStr + item.string.strip('\n\r')

                curQuestion['question'] = questionStr

                firstAnswer = True
                curQuestion['answers'] = []
                for answer in questions.select('ol li'):
                    correctAnswer = False
                    if firstAnswer:
                        correctAnswer = True
                        firstAnswer = False

                    curQuestion['answers'].append({
                        'text': answer.get_text(),
                        'correct': correctAnswer
                    })
                questionsObject.append(curQuestion)


# Save Questions and Answers as JSON
json.dump(questionsObject, open(OUTPUT_JSON, 'w'))
