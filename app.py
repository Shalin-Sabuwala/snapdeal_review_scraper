import os
from flask import Flask, render_template, request, jsonify

from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import pymongo

app = Flask(__name__)

@app.route('/', methods=['GET'])
def homepage():
    return render_template('index.html')

@app.route('/scrap',methods=['POST'])
def scrip():
    if request.method == 'POST':

        DB_NAME = "Snapdeal_Scrapper"
        searchString = request.form['content'].replace(" ", "+")
        try:
            snapdealUrl="https://www.snapdeal.com/search?keyword="+searchString
            client = pymongo.MongoClient("mongodb+srv://root:root@cluster0.msza9.mongodb.net/{DB_NAME}?retryWrites=true&w=majority")
            dataBase = client[DB_NAME]
            collection = dataBase[searchString]
            reviews = dataBase[searchString].find({})
            if reviews.count() > 0:
                return render_template('results.html', reviews=reviews)
            else:
                uClient = uReq(snapdealUrl)
                snapdealPage = uClient.read()
                uClient.close()
                snapdeal_html = bs(snapdealPage, "html.parser")
                # print(myntra_html)
                bigboxes = snapdeal_html.findAll("a", {"class": "dp-widget-link"})
                del bigboxes[0:4]
                box = bigboxes[0]

                productLink = str(box['href'])

                # options = Options()
                # options.add_argument('--headless')  # background task; don't open a window
                # options.add_argument('--disable-gpu')
                # options.add_argument('--no-sandbox')  # I copied this, so IDK?
                # options.add_argument('--disable-dev-shm-usage')
                # driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)
                chrome_options = webdriver.ChromeOptions()
                chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--no-sandbox")
                driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"),
                                          chrome_options=chrome_options)

                driver.get(productLink)

                time.sleep(2)
                html = driver.page_source
                soup = bs(html, "html.parser" )

                commentboxes = soup.findAll("div", {"class": "commentlist first jsUserAction"})
                reviews = []
                for commentboxe in commentboxes:
                    name = commentboxe.find_all("div",{"class": "_reviewUserName"})
                    del name[0:1]
                    reviewerName=name[0]['title']

                    findDate = name[0].text.split("on", 1)

                    date = findDate[1]

                    reviewDescription = commentboxe.find_all("p", {'class': ''})

                    custComment = reviewDescription[0].text
                    reviewHead=commentboxe.find_all("div", {'class': 'head'})


                    commentHead = reviewHead[0].text
                    peopleHelpfull = commentboxe.find_all("span", {'class': 'hf-num'})

                    reviewHelpfullByPeople=peopleHelpfull[0].text
                    reviewStar = commentboxe.findAll("i", {'class': 'sd-icon sd-icon-star active'})

                    rating = str(len(reviewStar))

                    mydict = {"Product": searchString, "Name": reviewerName, "Rating": rating, "CommentHead": commentHead,
                              "Comment": custComment,"Date":date,"PeopleHelpfull":reviewHelpfullByPeople}  # saving that detail to a dictionary


                    reviews.append(mydict)

            rec = collection.insert_many(reviews)
            return render_template('results.html', reviews=reviews)
        except Exception as e:

            return e


if __name__ == "__main__":
    app.run()
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
