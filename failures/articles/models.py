import datetime
import io
import logging
from typing import Optional

import feedparser
import numpy
import numpy as np
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from newsplease import NewsPlease
from newspaper import Article as NewsScraper
from bs4 import BeautifulSoup
import requests
import re

from failures.networks.models import (
    Embedder,
    QuestionAnswerer,
    Summarizer,
    ZeroShotClassifier,
    ChatGPT,
    SummarizerGPT,
    ClassifierChatGPT,
)

from failures.parameters.models import Parameter


class SearchQuery(models.Model):
    keyword = models.CharField(
        _("Keyword"),
        max_length=255,
        help_text=_("Keyword to use for searching for news articles."),
    )

    start_year = models.IntegerField(
        _("Start Year"),
        null=True,
        blank=True,
        help_text=_(
            "News articles will be searched from this year onwards. This field is optional."
        ),
    )

    end_year = models.IntegerField(
        _("End Year"),
        null=True,
        blank=True,
        help_text=_(
            "News articles will be searched until this year. This field is optional."
        ),
    )

    start_month = models.IntegerField(
        _("Start Month"),
        null=True,
        blank=True,
        help_text=_(
            "News articles will be searched from this month onwards. This field is optional."
        ),
    )

    end_month = models.IntegerField(
        _("End Month"),
        null=True,
        blank=True,
        help_text=_(
            "News articles will be searched until this month. This field is optional."
        ),
    )

    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True,
        help_text=_("Date and time when this search query was created."),
        editable=False,
    )

    last_searched_at = models.DateTimeField(
        _("Last Searched At"),
        null=True,
        blank=True,
        help_text=_("Date and time when this search query was last searched."),
        editable=False,
    )

    sources = ArrayField(
        models.URLField(max_length=255),
        blank=True,
        null=True,
        verbose_name=_("Sources"),
        help_text=_("Sources to search for news articles, such as nytimes.com,wired.com."),
    )

    class Meta:
        verbose_name = _("Search Query")
        verbose_name_plural = _("Search Queries")

    def __str__(self):
        return f"{self.keyword}"


class Article(models.Model):
    '''
    failures = models.ManyToManyField(
        "Failure",
        related_name="articles",
        related_query_name="article",
        verbose_name=_("Failures"),
    )
    '''

    search_queries = models.ManyToManyField(
        SearchQuery,
        related_name="articles",
        related_query_name="article",
        verbose_name=_("Search Queries"),
    )

    '''
    # TODO: Change arbitrary max_length constraints
    title = models.CharField(
        _("Title"), max_length=510, help_text=_("Title of the article.")
    )
    '''

    # Marking url as unique=True because we don't want to store the same article twice
    url = models.URLField(
        _("URL"), unique=True, max_length=510, help_text=_("URL of the article.")
    )

    published = models.DateTimeField(
        _("Published"), help_text=_("Date and time when the article was published.")
    )

    source = models.URLField(
        _("Source"),
        help_text=_("URL of the source of the article, such as nytimes.com."),
    )

    '''
    summary = models.TextField(
        _("Summary"),
        blank=True,
        help_text=_("Summary of the article generated by a summarizer model."),
    )
    '''

    body = models.TextField(
        _("Body"), blank=True, help_text=_("Body of the article scraped from the URL.")
    )

    embedding = models.FileField(
        _("Embedding"),
        upload_to="embeddings",
        null=True,
        help_text=_("NumPy array of the embedding of the article stored as a file."),
        editable=False,
    )

    scraped_at = models.DateTimeField(
        _("Scraped at"),
        auto_now_add=True,
        help_text=_("Date and time when the article was scraped."),
        editable=False,
    )

    '''
    describes_failure_os = models.BooleanField(
        _("Describes Failure OS"),
        null=True,
        help_text=_(
            "Whether the article describes a failure. This field is set by an open-source classifier."
        ),
    )
    '''

    describes_failure = models.BooleanField(
        _("Describes Failure"),
        null=True,
        help_text=_(
            "Whether the article describes a failure. This field is set by ChatGPT."
        ),
    )

    '''
    describes_failure_confidence = models.FloatField(
        _("Describes Failure Confidence"),
        null=True,
        help_text=_(
            "Confidence of the classifier in whether the article describes a failure."
        ),
    )
    '''

    summary_init = models.TextField(
        _("Classifier Summary"), 
        blank=True, null=True,
        help_text=_(
            "Summary of article to run through classifier to check if article describes a software failure."
        ),
    )
    
    headline = models.TextField(_("Headline"), blank=True, null=True)
    
    #Open ended postmortem fields
    title = models.TextField(_("Title"), blank=True, null=True)
    summary = models.TextField(_("Summary"), blank=True, null=True)
    system = models.TextField(_("System"), blank=True, null=True)
    time = models.TextField(_("Time"), blank=True, null=True)
    SEcauses = models.TextField(_("Software Causes"), blank=True, null=True)
    NSEcauses = models.TextField(_("Non-Software Causes"), blank=True, null=True)
    impacts = models.TextField(_("Impacts"), blank=True, null=True)
    mitigations = models.TextField(_("Mitigations"), blank=True, null=True)

    #Taxonomy fields: Options
    phase_option = models.TextField(_("Phase Option"), blank=True, null=True)
    boundary_option = models.TextField(_("Boundary Option"), blank=True, null=True)
    nature_option = models.TextField(_("Nature Option"), blank=True, null=True)
    dimension_option = models.TextField(_("Dimension Option"), blank=True, null=True)
    objective_option = models.TextField(_("Objective Option"), blank=True, null=True)
    intent_option = models.TextField(_("Intent Option"), blank=True, null=True)
    capability_option = models.TextField(_("Capability Option"), blank=True, null=True)
    duration_option = models.TextField(_("Duration Option"), blank=True, null=True)
    domain_option = models.TextField(_("Domain Option"), blank=True, null=True)
    cps_option = models.TextField(_("CPS Option"), blank=True, null=True)
    perception_option = models.TextField(_("Perception Option"), blank=True, null=True)
    communication_option = models.TextField(_("Communication Option"), blank=True, null=True)
    application_option = models.TextField(_("Application Option"), blank=True, null=True)
    behaviour_option = models.TextField(_("Behaviour Option"), blank=True, null=True)
    

    #Taxonomy fields: Explanations
    phase_rationale = models.TextField(_("Phase Rationale"), blank=True, null=True)
    boundary_rationale = models.TextField(_("Boundary Rationale"), blank=True, null=True)
    nature_rationale = models.TextField(_("Nature Rationale"), blank=True, null=True)
    dimension_rationale = models.TextField(_("Dimension Rationale"), blank=True, null=True)
    objective_rationale = models.TextField(_("Objective Rationale"), blank=True, null=True)
    intent_rationale = models.TextField(_("Intent Rationale"), blank=True, null=True)
    capability_rationale = models.TextField(_("Capability Rationale"), blank=True, null=True)
    duration_rationale = models.TextField(_("Duration Rationale"), blank=True, null=True)
    domain_rationale = models.TextField(_("Domain Rationale"), blank=True, null=True)
    cps_rationale = models.TextField(_("CPS Rationale"), blank=True, null=True)
    perception_rationale = models.TextField(_("Perception Rationale"), blank=True, null=True)
    communication_rationale = models.TextField(_("Communication Rationale"), blank=True, null=True)
    application_rationale = models.TextField(_("Application Rationale"), blank=True, null=True)
    behaviour_rationale = models.TextField(_("Behaviour Rationale"), blank=True, null=True)


    class Meta:
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")

    def __str__(self):
        return self.headline

    def has_manual_annotation(self) -> bool:
        return self.failures.filter(manual_annotation=True).exists()

    @classmethod
    def create_from_google_news_rss_feed(
        cls,
        search_query: SearchQuery,
    ):
        url = cls.format_google_news_rss_url(
            search_query.keyword,
            search_query.start_year,
            search_query.end_year,
            search_query.start_month,
            search_query.end_month,
            search_query.sources,
        )
        articles = []
        feed = feedparser.parse(url)
        search_query.last_searched_at = datetime.datetime.now()
        search_query.save()
        for entry in feed.entries:
            # TODO: reduce queries here
            # Continue if "opinion" in title
            if "opinion" in entry["title"].lower():
                continue
            dest_url = requests.get(entry.link) 
            dest_url = dest_url.url
            if not cls.objects.filter(url=dest_url).exists():
                article = cls.objects.create(
                    headline=entry["title"],
                    url=dest_url,
                    # example: Mon, 24 Oct 2022 11:00:00 GMT
                    published=datetime.datetime.strptime(
                        entry["published"], "%a, %d %b %Y %H:%M:%S %Z"
                    ),
                    source=entry["source"]["href"],
                )
                logging.info("Created article: %s.", article)
            else:
                article = cls.objects.get(url=dest_url)
            logging.info(
                f"Adding search query to article: %s - %s.", article, search_query
            )
            article.search_queries.add(search_query)
            article.save()
            articles.append(article)
        return articles

    # TODO: should this method be on SearchQuery?
    @staticmethod
    def format_google_news_rss_url(
        keyword: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_month: Optional[int] = None,
        end_month: Optional[int] = None,
        sources: Optional[list[str]] = None,
    ) -> str:
        keyword = keyword.replace(" ", "%20")
        url = f"https://news.google.com/rss/search?q={keyword}"
        if start_year:
            url += f"%20after%3A{start_year}-{start_month}-01"
        if end_year:
            url += f"%20before%3A{end_year}-{end_month}-01" #TODO: Remove 15
        for i, source in enumerate(sources):
            if i > 0:
                url += "%20OR"
            url += f"%20site%3Ahttps%3A%2F%2F{source}"
        url += "&hl=en-US&gl=US&ceid=US%3Aen"
        return url

    #TODO: Cleanup
    '''
    def scrape_body(self):
        try:
            article = NewsPlease.from_url(self.url)
        except Exception as e:
            logging.error(f"Failed to scrape article %s: %s.", self, e)
            return
        if article.maintext is None:
            logging.error("Failed to scrape article %s: No text found.", self)
            return
        self.body = article.maintext
        self.save()
        logging.info(f"Scraped body for %s.", self)
        return self.body
    '''
    def scrape_body(self):
        try:
            #dest_url = requests.get(self.url) #TODO: Need to move this earlier, because this is how we check if an article already exists
            #self.url = dest_url.url
            article_scrape = NewsScraper(self.url)
            article_scrape.download()
            article_scrape.parse()
            article_text = self.preprocess_html(article_scrape)
        except Exception as e:
            logging.error(f"Failed to scrape article %s: %s.", self, e)
            return
        if article_text is None:
            logging.error("Failed to scrape article %s: No text found.", self)
            return
        self.body = article_text
        self.save()
        logging.info(f"Scraped body for %s.", self)
        return self.body
    
    def preprocess_html(self, article_scrape):
        logging.info(f"Processing html for %s.", self)
        # HTML string
        html_string = article_scrape.html
        article_text = None

        # Create a BeautifulSoup object
        soup = BeautifulSoup(html_string, 'html.parser')

        #Scrape text from WIRED
        if "wired" in article_scrape.url:
            article_div = soup.find_all("div", attrs={"class": "body__inner-container"})
            article_text = ""
            for text in article_div:
                article_text = article_text + " " + text.get_text(separator=' ')

        #Scrape text from NYT
        elif "nytimes" in article_scrape.url:
            article_div = soup.find_all("section", attrs={"name": "articleBody"})
            article_text = ""
            for text in article_div:
                article_text = article_text + " " + text.get_text(separator=' ')

        else:
            logging.info("URL is not NYT or WIRED: " + article_scrape.url + " for article: " + str(self))
            article_text = article_scrape.text
        
        if article_text is None or len(article_text.split()) < 100:
            logging.info("Issue parsing: " + article_scrape.url + " for article: " + str(self))
            article_text = article_scrape.text

        article_text = "Published on " + str(article_scrape.publish_date) + ". " + article_text

        return article_text

    def summarize_body(self, summarizer: Summarizer):
        self.summary: str = summarizer.run(self.body)
        self.save()
        return self.summary

    def create_embedding(self, embedder: Embedder):
        embedding = embedder.run(self.body)
        bytes_io = io.BytesIO()
        numpy.save(bytes_io, embedding)
        self.embedding.save("embedding.npy", bytes_io)
        self.save()
        return self.embedding

    def cosine_similarity(self, other: "Article") -> float:
        if self.embedding is None or other.embedding is None:
            raise ValueError("One or both articles have no embedding.")
        embedding_one = numpy.load(self.embedding.path)
        embedding_two = numpy.load(other.embedding.path)
        return np.dot(embedding_one, embedding_two) / (
            np.linalg.norm(embedding_one) * np.linalg.norm(embedding_two)
        )

    #Open source classifier
    def classify_as_failure_os(self, classifier: ZeroShotClassifier, labels: list[str]):
        classify_data = {"text": self.body, "labels": labels}
        prediction: tuple[str, float] = classifier.run(classify_data)
        self.describes_failure_os = classifier.labels.index(prediction[0]) == 0
        self.describes_failure_confidence = prediction[1]

        self.save()
        return self.describes_failure_os

    # GPT based classifier
    def classify_as_failure_ChatGPT(self, classifier: ClassifierChatGPT):

        #Truncate article if it is too long
        article_text = self.body.split()[:2750]

        content = "You will help classify whether this article describes a software failure: \n" + ' '.join(article_text)

        messages = [
                {"role": "system", 
                "content": content}
                ]

        prompt = "Does this article describe a software failure (software failure could mean a flaw, bug, mistake, anomaly, fault, error, exception, crash, glitch, defect, incident, side effect, or hack in software)?: " \
                + "\n" \
                + "Answer with just True or False"

        messages.append(
                        {"role": "user", "content": prompt },
                        )
        
        self.describes_failure_ChatGPT = classifier.run(messages)

        self.save()
        return self.describes_failure_ChatGPT


    def postmortem_from_article_ChatGPT(
        self,
        ChatGPT: ChatGPT,
        questions: dict,
        taxonomy_options: dict,
        query_all: bool,
    ): 

        logging.info("Extracting postmortem from article: %s.", self)

        
        article_body = self.body
        
        #Pre-process articles if they are too long
        article_len = len(article_body.split())
        print(article_len)
        if article_len > 2750:
            article_begin = article_body.split()[:-(article_len-2500)]
            article_end = article_body.split()[-(article_len-2500):]
                
            if len(article_end.split()) > 2750: #if the last part of article is too long, just truncate it
                article_end = article_end.split()[:2500]

            content = "You will summarize a part of an article."
            messages = [
                    {"role": "system", 
                    "content": content}
                    ]
            messages.append(
                            {"role": "user", "content": "summarize this text (retain information relevant to software failure) with a maximum of 500 words: " + ' '.join(article_end)},
                            )
        
            reply = ChatGPT.run(messages)

            article_body = ' '.join(article_begin) + reply
            logging.info("Reduced articled length for article: "+ str(self) + "; Old length: " + str(article_len) + " ; New length: " + str(len(article_body.split())) )


        #Create postmortems
        content = "You will answer questions about a software failure (failure could mean a flaw, bug, mistake, anomaly, fault, error, exception, crash, glitch, defect, incident, side effect, or hack) described in this article: " + article_body

        postmortem = {}
        for question_key in list(questions.keys()): #[list(questions.keys())[i] for i in [0,2,4,8,16,21]]: #list(questions.keys()):
            
            #Check if the question has already been answered
            answer_set = True
            if question_key in taxonomy_options.keys():
                question_option_key = question_key + "_option"
                question_rationale_key = question_key + "_rationale"
                if not getattr(self, question_option_key):
                    answer_set = False
            else:
                if not getattr(self, question_key):
                    answer_set = False


            if query_all or not answer_set: 

                logging.info("Querying question: " + str(question_key))

                messages = [
                        {"role": "system", 
                        "content": content}
                        ]
                messages.append(
                                {"role": "user", "content": questions[question_key]},
                                )
                reply = ChatGPT.run(messages)

                if "{" and "}" in reply:
                    try:
                        #logging.info("Found json")

                        # extract the values for "explanation" and "option" using capturing groups
                        match = re.search(r'{"explanation": "(.*)", "option": (.*)}', reply)
                        # sanitize the values if there're quotes
                        explanation = match.group(1).replace('"', '\\"')
                        option = match.group(2).replace('"', '')
                        try:
                            #logging.info("Trying to catch option")
                            option_value = taxonomy_options[question_key][option]
                        except:
                            logging.info("Option error")
                            option_value = option

                        reply = {"explanation": explanation,
                                    "option": option_value.lower()
                                    }
                        
                        #if response json is in incorrect format
                    except:
                        logging.info("Incorrect json form")
                        #logging.info(type(reply))
                        reply = reply
                else:

                    reply = reply

                if question_key in taxonomy_options.keys():
                    setattr(self, question_option_key, reply['option'])
                    setattr(self, question_rationale_key, reply['explanation'])
                else:
                    setattr(self, question_key, reply)


        '''
                postmortem[question_key] = reply
        

        #Assign the postmortem to the failure #TODO: Create a struct, failure.title.prompt and failure.title.response - so that you only need to update at one place
        self.title           = postmortem['title']
        self.summary         = postmortem['summary']
        self.system          = postmortem['system']
        self.time            = postmortem['time']
        self.SEcauses        = postmortem['SEcauses']
        self.NSEcauses       = postmortem['NSEcauses']
        self.impacts         = postmortem['impacts']
        self.mitigations     = postmortem['mitigations']
        
        self.phase_option = postmortem['phase']['option']  #str(postmortem['phase']['option'])]
        self.boundary_option = postmortem['boundary']['option']
        self.nature_option = postmortem['nature']['option']
        self.dimension_option = postmortem['dimension']['option']
        self.objective_option = postmortem['objective']['option']
        self.intent_option = postmortem['intent']['option']
        self.capability_option = postmortem['capability']['option']
        self.duration_option = postmortem['duration']['option']
        self.domain_option = postmortem['domain']['option']
        self.cps_option = postmortem['cps']['option']
        self.perception_option = postmortem['perception']['option']
        self.communication_option = postmortem['communication']['option']
        self.application_option = postmortem['application']['option']
        self.behaviour_option = postmortem['behaviour']['option']

        self.phase_rationale = postmortem['phase']['explanation']
        self.boundary_rationale = postmortem['boundary']['explanation']
        self.nature_rationale = postmortem['nature']['explanation']
        self.dimension_rationale = postmortem['dimension']['explanation']
        self.objective_rationale = postmortem['objective']['explanation']
        self.intent_rationale = postmortem['intent']['explanation']
        self.capability_rationale = postmortem['capability']['explanation']
        self.duration_rationale = postmortem['duration']['explanation']
        self.domain_rationale = postmortem['domain']['explanation']
        self.cps_rationale = postmortem['cps']['explanation']
        self.perception_rationale = postmortem['perception']['explanation']
        self.communication_rationale = postmortem['communication']['explanation']
        self.application_rationale = postmortem['application']['explanation']
        self.behaviour_rationale = postmortem['behaviour']['explanation']

        '''
        #write a sanitization function to sanitize options: unknown, true, false
        self.save()

        return True


'''
class FailureCause(models.Model): #TODO: Not used 
    failure = models.ForeignKey(
        "Failure",
        related_name="failure_causes",
        related_query_name="failure_cause",
        on_delete=models.CASCADE,
        verbose_name=_("Failure"),
    )

    description = models.TextField(_("Description"))

    class Meta:
        verbose_name = _("Failure Cause")
        verbose_name_plural = _("Failure Causes")

    def __str__(self):
        return self.description
'''


class Failure(models.Model):

    failure = models.ForeignKey(Article, null=True, on_delete=models.SET_NULL)

    published = models.DateTimeField(_("Published"), help_text=_("Date and time when the article was published."), blank=True, null=True)
    #TODO: Find the earliest published date and use the month and year
    
    title = models.TextField(_("Title"), blank=True, null=True)
    summary = models.TextField(_("Summary"), blank=True, null=True)


    '''
    #Choices for taxonomy
    phase = [("0", 'system design'), ("1", 'operation'), ("2", 'both'), ("3", 'neither'), ("-1", 'unknown')]
    boundary = (('0', 'within the system'), ('1', 'outside the system'), ('2', 'both'), ('3', 'neither'), ('-1', 'unknown'))
    nature = (('0', 'human actions'), ('1', 'non human actions'), ('2', 'both'), ('3', 'neither'), ('-1', 'unknown'))
    dimension = (('0', 'hardware'), ('1', 'software'), ('2', 'both'), ('3', 'neither'), ('-1', 'unknown'))
    objective = (('0', 'malicious'), ('1', 'non-malicious'), ('2', 'both'), ('3', 'neither'), ('-1', 'unknown'))
    intent = (('0', 'deliberate'), ('1', 'accidental'), ('2', 'both'), ('3', 'neither'), ('-1', 'unknown'))
    capability = (('0', 'accidental'), ('1', 'development incompetence'), ('2', 'both'), ('3', 'neither'), ('-1', 'unknown'))
    duration = (('0', 'permanent'), ('1', 'temporary'), ('2', 'intermittent'), ('-1', 'unknown'))
    domain = (('0', 'automotive'), ('1', 'critical infrastructure'), ('2', 'healthcare'), ('3', 'energy'), ('4', 'transportation'), ('5', 'infrastructure'), ('6', 'aerospace'), ('7', 'telecommunications'), ('-1', 'unknown'))
    cps = (('true', 'true'), ('false', 'false'), ('-1', 'unknown'))
    perception = (('0', 'sensors'), ('1', 'actuators'), ('2', 'processing unit'), ('3', 'network communication'), ('4', 'embedded software'), ('-1', 'unknown'))
    communication = (('false', 'False'), ('1', 'link level'), ('2', 'connectivity level'), ('-1', 'unknown'))
    application = (('true', 'true'), ('false', 'false'), ('-1', 'unknown'))
    behaviour = (('0', 'crash'), ('1', 'omission'), ('2', 'timing'), ('3', 'value'), ('4', 'Byzantine fault'), ('-1', 'unknown'))
    
    #Taxonomy fields: Options
    phase_option = models.CharField(max_length=255, choices=phase, blank=True, null=True)
    boundary_option = models.CharField(max_length=255, choices=boundary, blank=True, null=True)
    nature_option = models.CharField(max_length=255, choices=nature, blank=True, null=True)
    dimension_option = models.CharField(max_length=255, choices=dimension, blank=True, null=True)
    objective_option = models.CharField(max_length=255, choices=objective, blank=True, null=True)
    intent_option = models.CharField(max_length=255, choices=intent, blank=True, null=True)
    capability_option = models.CharField(max_length=255, choices=capability, blank=True, null=True)
    duration_option = models.CharField(max_length=255, choices=duration, blank=True, null=True)
    domain_option = models.CharField(max_length=255, choices=domain, blank=True, null=True)
    cps_option = models.CharField(max_length=255, choices=cps, blank=True, null=True)
    perception_option = models.CharField(max_length=255, choices=perception, blank=True, null=True)
    communication_option = models.CharField(max_length=255, choices=communication, blank=True, null=True)
    application_option = models.CharField(max_length=255, choices=application, blank=True, null=True)
    behaviour_option = models.CharField(max_length=255, choices=behaviour, blank=True, null=True)
    '''



    #TODO: Cleanup
    '''
    class Duration(models.TextChoices):
        TRANSIENT = "TRANSIENT", _("Transient")
        PERMANENT = "PERMANENT", _("Permanent")
        INTERMITTENT = "INTERMITTENT", _("Intermittent")

    class Location(models.TextChoices):
        INTERNAL = "INTERNAL", _("Internal")
        EXTERNAL = "EXTERNAL", _("External")

    class Semantics(models.TextChoices):
        CRASH = "CRASH", _("Crash")
        OMISSION = "OMISSION", _("Omission")
        TIMING = "TIMING", _("Timing")
        VALUE = "VALUE", _("Value")
        ARBITRARY = "ARBITRARY", _("Arbitrary")

    class Behavior(models.TextChoices):
        SOFT = "SOFT", _("Soft")
        HARD = "HARD", _("Hard")

    class Dimension(models.TextChoices):
        SOFTWARE = "SOFTWARE", _("Software")
        HARDWARE = "HARDWARE", _("Hardware")

    name = models.CharField(_("Name"), max_length=255)

    description = models.TextField(_("Description"))

    started_at = models.CharField(_("Started at"), max_length=255)

    ended_at = models.CharField(_("Ended at"), max_length=255)

    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)

    # manual_annotation=False means that the failure was automatically detected
    manual_annotation = models.BooleanField(_("Manual Annotation"), default=False)

    # display means that this failure should be displayed in the UI, because it has been merged with other failures
    display = models.BooleanField(_("Display"), default=False)

    industry = models.CharField(_("Industry"), max_length=255)

    duration = models.CharField(
        _("Duration"),
        max_length=12,
        choices=Duration.choices,
        blank=True,
    )

    location = models.CharField(
        _("Location"),
        max_length=8,
        choices=Location.choices,
        blank=True,
    )

    semantics = models.CharField(
        _("Semantics"),
        max_length=9,
        choices=Semantics.choices,
        blank=True,
    )

    behavior = models.CharField(
        _("Behavior"),
        max_length=4,
        choices=Behavior.choices,
        blank=True,
    )

    dimension = models.CharField(
        _("Dimension"),
        max_length=8,
        choices=Dimension.choices,
        blank=True,
    )
    '''

    class Meta:
        verbose_name = _("Failure")
        verbose_name_plural = _("Failures")

    def __str__(self):
        return self.title

    #TODO: Cleanup
    '''
    @classmethod
    def create_from_article(
        cls,
        article: Article,
        question_answerer: QuestionAnswerer,
    ):
        failure = cls()

        logging.info("Extracting postmortem from article: %s.", article)

        failure.name = question_answerer.run(
            (Parameter.get("FAILURE_NAME_QUESTION", "What is the name of the software failure?"), article.body)
        )
        failure.industry = question_answerer.run(
            (Parameter.get("FAILURE_INDUSTRY_QUESTION", "What industry does this software failure belong to?"), article.body)
        )
        failure.started_at = question_answerer.run(
            (Parameter.get("FAILURE_STARTED_AT_QUESTION", "When did this software failure start?"), article.body)
        )
        failure.ended_at = question_answerer.run(
            (Parameter.get("FAILURE_ENDED_AT_QUESTION", "When did this software failure end?"), article.body)
        )
        failure.description = question_answerer.run(
            (Parameter.get("FAILURE_DESCRIPTION_QUESTION", "What is the description of the software failure?"), article.body)
        )
        failure.save()
        return failure
    '''

