# remember to credit They Said So Quotes API
import datetime
import os
import sqlite3
import time
import re
import urllib.error

import mysql.connector
from random import randrange
import json
from urllib.request import urlopen
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivymd.uix.picker import MDThemePicker
import random
import requests
from kivmob import KivMob, TestIds
from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.metrics import dp
from kivy.storage.jsonstore import JsonStore
from kivy.utils import rgba, platform
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty
from kivymd.app import MDApp
from kivy.core.window import Window
from kivymd.toast import toast
from kivymd.uix.button import MDFlatButton, MDFillRoundFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.picker import MDDatePicker
from kivymd.uix.snackbar import Snackbar

from database import Database
# Initialize db instance
db = Database()
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.list import TwoLineAvatarIconListItem, ILeftBodyTouch
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.behaviors import FakeRectangularElevationBehavior

if platform == "android":
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])

#Window.size = (320, 620)


class DilayAffirmationCard(MDCard):
    affirmation_text = StringProperty()
    affirmation_image = StringProperty()


class MenuProfileImage(Image, Button):
    pass


class HomeSearchDialogContent(MDFloatLayout):
    pass


class AffirmationSearchDialogContent(MDFloatLayout):
    affirmation_text = StringProperty()
    affirmation_image = StringProperty()


class WeatherSearchDialogContent(MDFloatLayout):
    pass


class MostPopularMotivation(MDCard):
    most_popular_quotes_text = StringProperty()
    most_popular_quotes_author = StringProperty()
    most_popular_quote_bg_image = StringProperty()


class ErrorDialogContent(MDFloatLayout):
    pass


class QuotesForTheDayImageCard(MDCard):
    quotes_for_the_day_text = StringProperty()
    quotes_for_the_day_author = StringProperty()
    quote_bg_image = StringProperty()


class QuotesOfTheDaycard(MDCard):
    qoute_of_the_day_text = StringProperty()
    quote_of_the_day_author = StringProperty()


class NavBar(FakeRectangularElevationBehavior, MDBoxLayout):
    pass


class Content_delete_dialog(MDFloatLayout):
    def __init__(self, pk=None, **kwargs):
        super().__init__(**kwargs)
        # state a pk which we shall use link the list items with the database primary keys
        self.pk = pk

    def delete_task_item(self, the_list_item):
        '''Delete the task'''
        try:
            self.parent.remove_widget(the_list_item)
            db.delete_task(the_list_item.pk)  # Here
        except NameError:
            toast("deleting.....")


# create the following two classes
class ListItemWithCheckbox(FakeRectangularElevationBehavior, MDFloatLayout, TwoLineAvatarIconListItem):
    text = StringProperty()
    secondary_text = StringProperty()
    delete_dialog = None
    #pending = NumericProperty(0)
    #completed = NumericProperty(0)
    #all_tasks = NumericProperty(0)
    #del_dialog = StringProperty()
    '''Custom list item'''

    def __init__(self, pk=None, **kwargs):
        super().__init__(**kwargs)
        # state a pk which we shall use link the list items with the database primary keys
        self.del_dialog = None
        self.pk = pk

    def mark(self, check, the_list_item):
        '''mark the task as complete or incomplete'''
        if check.active == True:
            # add strikethrough to the text if the checkbox is active
            the_list_item.text = '[s]' + the_list_item.text + '[/s]'
            db.mark_task_as_complete(the_list_item.pk)  # here
        else:
            # we shall add code to remove the strikethrough later
            the_list_item.text = str(db.mark_task_as_incomplete(the_list_item.pk)) #

    def delete_item(self, the_list_item):
        '''Delete the task'''
        #the_list_item = self.ids.the_list_item
        self.parent.remove_widget(the_list_item)
        db.delete_task(the_list_item.pk)  # Here

    def show_delete_dialog(self, obj):
        self.md_dailog = MDDialog(title="Delete Tasks",text="are sure you want to delete this tasks",
                         size_hint=[.75,.6],
                         buttons=[
                             MDFlatButton(
                                 text="CANCEL",
                                 theme_text_color="Custom",
                                 text_color=self.theme_cls.accent_color,
                                 on_press=self.close_md_dialog
                             ),
                             MDFillRoundFlatButton(
                                 text="DELETE",
                                 md_bg_color=(255/255,76/255,48/255,255),
                                 on_release=self.delete_item,
                             ),
                         ],
                         )
        self.md_dailog.open()

    def close_md_dialog(self, obj):
        self.md_dailog.dismiss()


class LeftCheckbox(ILeftBodyTouch, MDCheckbox):
    '''Custom left container'''


class DialogContent(MDBoxLayout):
    """OPENS A DAILOG BOX THAT GETS THE TASK FROM THE USER"""
    def __init__(self, **kwargs):
        super().__init__(*kwargs)
        # set the date_text label to today's date when user first opens the dailog
        self.ids.date_text.text = str(datetime.datetime.now().strftime('%A %d %B %Y'))

    def show_date_picker(self):
        """Opens the date picker"""
        date_dialog = MDDatePicker()
        date_dialog.bind(on_save=self.on_save)
        date_dialog.open()

    def on_save(self, instance, value, date_range):
        """This functions gets the date from the date picker and converts its it a
        more friendly form then changes the date label on the dialog to that"""

        date = value.strftime('%A %d %B %Y')
        self.ids.date_text.text = str(date)


class AdviceContent(MDFloatLayout):
    pass


class LoadingDialog(MDFloatLayout):
    pass


class XtrA(MDApp):
    task_list_dialog = None
    delete_task_dialog = None
    error_dialog = None
    home_search_dialog = None
    advice_dialog = None
    search_weather_dialog = None
    search_affirmation_dialog = None
    pending = NumericProperty(0)
    dialog2 = None
    dialog1 = None
    loading_dialog = None
    completed = NumericProperty(0)
    all_tasks = NumericProperty(0)
    weight = NumericProperty(12)
    age = NumericProperty(18)
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    mydatabase = mysql.connector.Connect(host="localhost", user="root", password="60587102", database="loginform")
    cursor = mydatabase.cursor()
    cursor.execute("select * from logindata")
    for i in cursor.fetchall():
        print(i[0], i[1])
    user_store = JsonStore('user_details.json')
    task_progress = JsonStore('user_task_progress.json')

    def build(self):
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.accent_palette = "Red"

        self.ads = KivMob('ca-app-pub-3940256099942544~3347511713')
        self.ads.new_banner('ca-app-pub-3940256099942544/6300978111', top_pos=False)
        self.ads.request_banner()
        self.ads.new_interstitial('ca-app-pub-3940256099942544/1033173712')
        self.ads.request_interstitial()
        # create table for theme picker
        theme_connect = sqlite3.connect('myapp.db')
        theme_cursor = theme_connect.cursor()
        theme_cursor.execute("""CREATE TABLE IF NOT EXISTS theme(primary_palette TEXT NOT NULL, accent_palette TEXT NOT NULL, theme_style TEXT NOT NULL)
        """)

        theme_connect.commit()
        theme_connect.close()

        # create database or connect to one
        conn = sqlite3.connect('database.db')

        # create a cursor
        c = conn.cursor()

        # create a table
        c.execute("""CREATE TABLE if not exists tasks_status(name text)""")

        # commit our changes
        conn.commit()

        # close our connection
        conn.close()

        global screen_manager
        screen_manager = ScreenManager()
        return Builder.load_file('main.kv')

    def update_tasks_progress(self):
        self.task_progress = JsonStore('user_task_progress.json')
        self.task_progress.put('tasker', pending=self.pending,
                       complete=self.completed,
                       total_tasks=self.all_tasks)

    def show_tasks_progress(self):
        self.pending = self.task_progress.get('tasker')['pending']
        self.completed = self.task_progress.get('tasker')['complete']
        self.all_tasks = self.task_progress.get('tasker')['total_tasks']

    def add_pending(self):
        self.pending = self.pending + 1
        self.all_tasks = self.all_tasks + 1
        self.update_tasks_progress()
        self.show_tasks_progress()

    def add_completed(self, check, the_list_item):
        if check.active == True:
            self.completed = self.completed + 1
            self.pending = self.pending - 1
            self.update_tasks_progress()
            self.show_tasks_progress()
        else:
            self.completed = self.completed - 1
            self.pending = self.pending + 1
            self.update_tasks_progress()
            self.show_tasks_progress()

    def progress_after_delete(self, check, the_list_item):
        if check.active == True:
            self.completed = self.completed - 1
            self.all_tasks = self.all_tasks - 1
            self.update_tasks_progress()
            self.show_tasks_progress()
        else:
            self.all_tasks = self.all_tasks - 1
            self.pending = self.pending - 1
            self.update_tasks_progress()
            self.show_tasks_progress()

    def __init__(self, pk=None, **kwargs):
        super().__init__(**kwargs)
        # state a pk which we shall use link the list items with the database primary keys
        self.pk = pk

    def delete_task_item(self, the_list_item):
        '''Delete the task'''
        try:
            self.root.ids.container.remove_widget(ListItemWithCheckbox)
            db.delete_task(the_list_item.pk)  # Here
        except NameError:
            toast("Error can't delete task.....")

    def text(self):
        api_key = "PKdyDYuaaEZ2vwwPogR8WA==8LPK2F0HaIMSXkP4"
        api_url = 'https://api.api-ninjas.com/v1/quotes?'
        response = requests.get(api_url, headers={'X-Api-Key': 'PKdyDYuaaEZ2vwwPogR8WA==8LPK2F0HaIMSXkP4'})
        res = response.json()

    def show_loading_dialog(self, *args):
        if not self.loading_dialog:
            self.loading_dialog = MDDialog(
                type="custom",
                auto_dismiss=False,
                content_cls=LoadingDialog(),
                md_bg_color=rgba(randrange(200), randrange(200), randrange(200), 255)

            )
        self.loading_dialog.open()

    def close_loading_dialog(self, *args):
        self.loading_dialog.dismiss()

    def get_affirmed1(self, instance):
        affirmation_layout = self.root.ids.affirmation_layout

        self.root.ids.affirmation_layout.clear_widgets()
        affirmation_bg_image = ["motivation_images/accessories.jpg", "motivation_images/motivation_image4.jpg",
             "motivation_images/motivation_image5.jpg", "motivation_images/motiv3.jpg", "motivation_images/motiv2.jpg",
             "motivation_images/motivation_image3.jpg", "motivation_images/motiv2.jpg",
             "motivation_images/motivation_image7.jpg", "motivation_images/motivation_image8.jpg",
             "motivation_images/motivation_image9.jpg", "motivation_images/motivation_image10.jpg",
             "motivation_images/motivation_image11.jpg",
             "motivation_images/motivation_image13.jpg", "motivation_images/motivation_image14.jpg",
             "motivation_images/motivation_image15.jpg", "motivation_images/motivation_image16.jpg",
             "motivation_images/motivation_image17.jpg", "motivation_images/motivation_image18.jpg",
             "motivation_images/motivation_image19.jpg", "motivation_images/motivation_image21.jpg",
             "motivation_images/motivation_image22.jpg", "motivation_images/motivation_image23.jpg",
             "motivation_images/motivation_image24.jpg", "motivation_images/motivation_image25.jpg",
             "motivation_images/motivation_image29.jpg", ]

        women = ["I am learning to be a better wife with each new day.",
                               "I am learning to be a better mother with each new day.",
                               "I am learning to be a better daughter with each new day.",
                               "I embrace being a positive, joyful, playful woman.",
                               "My courage is a strong tower that surrounds me. I transform problems into challenges, weaknesses into strengths, and fear into action.",
                               "I am capable.", "I am intelligent.", "I am innovative.", "I am brave.", "I am brave.",
                               "I am confident.", "I stand up for myself.", "I can do hard things.",
                               "I am in charge of my own identity.", "I have faith in myself.", "My ideas are powerful",
                               "I am allowed to change my mind.", "This is my time.", "I am articulate",
                               "I know myself.", "I am an independent person.", "I am good at many things.",
                               "Anything is possible in my life.", "I have faith in my own abilities.",
                               "I am qualified to be where I am.", "I make good decisions.",
                               "I will stop apologizing for things I can’t control.", "I am ready to learn and grow.",
                               "Failure is not negative.", "I know I can do this.", "Today I will take the first step.",
                               "I am ambitious.", "I am better than I was yesterday.", "I enjoy learning.",
                               "I am proud of the person I am becoming.", "I am my own biggest cheerleader.",
                               "I am constantly learning.", "I am working hard to better myself.",
                               "I am filled with focus.", "Every day is an opportunity for greatness.",
                               "I allow myself to evolve.", "My dreams are coming true."]

        man = ["I am successful.", "I am brave.", "I bravely strive to better myself.", "I am in touch with my emotions.",
             "I balance my masculine and feminine energies.", "I surrender to the universe.", "My emotions are worthy.",
             "I am worthy of love.", "I love myself.", "I am resilient.", "I can change my thoughts.",
             "I can’t control others.", "Every day is an opportunity for greatness." ]

        relationship = ["I am in charge of my emotions and my decisions",
                                      "I am in a loving relationship filled with unconditional love, trust, and respect.",
                                      "I have a wonderful partner, and we are both happy and at peace.",
                                      "I am in a joyous intimate relationship with a person who truly loves me.",
                                      "I enjoy the time I spend with my spouse and we have fun together",
                                      "I love that my marriage is becoming deeper, stronger, and more loving every day.",
                                      "I love that my relationship is becoming more romantic every day.",
                                      "I enjoy being loved and treasured by my amazing, kind, and generous partner.",
                                      "I am the best friend anyone can have because I am loyal, loving, and understanding.",
                                      " I choose friends who love me the way I am and approve of me.",
                                      " I show my family how much I love them in every way possible – both verbal and non-verbal.",
                                      "I forgive everyone in my past for all perceived wrongs. I release them with love." ]

        success = ["I am a money magnet. Money flows to me easily and effortlessly.",
                                 "I am open and receptive to all the wealth life offers me.",
                                 "I use money to better my life and the lives of others.",
                                 " I constantly attract opportunities that create more money.",
                                 " My finances improve beyond my wildest dreams.",
                                 "Every day in every way, I receive more and more money.",
                                 "Whatever activities I perform make money for me and I am always full of money.",
                                 "Every day I am attracting and saving more and more money.",
                                 "I attract money naturally. My middle name is money.",
                                 "I am deserving of abundance in my life.", "I am open to receive wealth in many ways",
                                 "The more I give, the more I receive. The more I receive, the more I give.",
                                 "My life is full of love and joy and all the material things that I need",
                                 "Prosperity overflows in my life. I have everything in abundance.",
                                 "I allow all good things to come into my life and I enjoy them.",
                                 "Right now, I accept the abundance that is flowing into my life",
                                 "I celebrate the abundance of others knowing that my joy in celebration increases my own abundance",
                                 "I am successful.", "I am a magnet for success.",
                                 "Love, health and success are attracted to me.",
                                 "I have unstoppable confidence within me.", "Life just feels great all of the time.",
                                 "There is always a way if I am committed.",
                                 "I am so excited because all of my dreams are coming true.",
                                 "Great things always seem to come my way.", "I am a naturally happy person.",
                                 "I am a naturally confident person.", "I am a naturally confident person.",
                                 "Opportunities just seem to fall right into my lap.", "I am full of energy and life",
                                 "I am a good person who deserves success and happiness.",
                                 "I love myself for who I am.", "Everything always works out for me.",
                                 "I am highly motivated and productive.",
                                 "It doesn’t matter what others think of me, for I know who I am.",
                                 "I am a centre for positivity, joy and love.",
                                 "I am incredibly grateful for all of my success.",
                                 "I use positive thinking to manifest a positive life.",
                                 "I choose to think positive and create a wonderful life for myself.",
                                 "I find it easy to succeed at everything I do.",
                                 "People look at me and wonder how I so naturally attract success.", "I think BIG.",
                                 "I act fearlessly.", "The universe always provides for me.",
                                 "I am so happy and grateful for my life.",
                                 "Things have a way of working themselves out.", "I have such an amazing life.",
                                 "I am so lucky.  Life is rigged in my favour.", "I love who I am and I love my life.",
                                 "My goals and dreams always come true.",
                                 "I am passionate about constantly being better and more successful.",
                                 "Somehow the universe just always helps me achieve my goals.",
                                 "My dreams are materializing before my very eyes.",
                                 "The wealth of the universe is circulating in my life and flowing to me in avalanches of prosperity.",
                                 "Money wants me.", "I am very motivated, driven and ambitious.",
                                 "I can easily pick myself up and lift my spirits when needed.",
                                 "I find it easy to be optimistic.",
                                 "I only permit positive thoughts to remain in my mind.", "Wealth is all around me.",
                                 "I am surrounded by abundance.", "When I go after what I want, it comes to me.",
                                 "My mind is a magnet for all good things.", "I have success in all areas of my life.",
                                 "I am grateful that I am so healthy, happy and successful.",
                                 "Success comes naturally to me.", "Everything I do always results in great success.",
                                 "I can never fail, for everything that happens contributes to me being better.",
                                 "The seeds of my greatness lie in my mind.",
                                 "I am love, health and wealth.", "My affirmations for success always bear fruit.",
                                 "Others are inspired by my success.", "I am incredibly successful.",
                                 "I am decisive, confident and take action.", "It is so easy to achieve my goals.",
                                 "The universe is friendly and helps me to achieve my dreams.",
                                 "Right now, I am exactly what and where I want to be.",
                                 "Others are attracted to me because I am always successful.",
                                 "I continuously enhance all areas of my life.",
                                 "Life just keeps getting better and better.",
                                 "Every day I move closer to my goals and dreams.",
                                 "I am resilient, persistent and dedicated.",
                                 "I have the will and desire to reach unlimited heights of success."]

        hope_confidence_positive_happiness = [" Every day is a new day full of hopes, happiness, and possibilities",
             "As I say yes to life, life says yes to me", " I claim my power and move beyond all limitations.",
             " I am beautiful, and everybody loves me",
             "I am very thankful for all the love in my life. I find it everywhere.",
             "I am greeted by love wherever I go.", "I am safe in the Universe and All Life loves and supports me.",
             " My thoughts are my reality so I think up a bright new day.",
             " There is plenty for everyone, and we bless and prosper each other",
             " When my intentions are clear, the Universe cooperates with me and I can accomplish anything.",
             "I think of only positive things and positive things happen in my life.",
             "I am full of energy and hope and live my life to the fullest",
             "Motivation comes to me from inside. I am my own motivator.",
             "I know that I have the knowledge and resources to achieve my dreams",
             "I fully accept myself and know that I am worthy of great things in life.",
             "I am destined for big success in life.",
             "I am recognized as an expert in my industry for my pioneering work.", "I have a strong inner confidence.",
             "Being self-confidant allows me to do great things.",
             "I am strong, independent and able to manifest my dreams.", "I believe in myself",
             "I let go of all self-doubts and replace them with a positive self-image.",
             "Today I look for and appreciate the good.", "My body knows what’s best for my health and well-being.",
             "I welcome joy into my life.", "I attract the perfect people at the right time.",
             "Something wonderful is always on the verge of happening.",
             "I have the power to change my story.", "I accept myself just as I am.",
             "The world and my reality is my playground, and I am in charge of them.",
             "I am strong and I get stronger day by day.", "I am proud of myself.",
             "I can do anything I put my mind to.", "I’m always willing to learn.",
             "I embrace and accept change. Change is good and helps me to grow.",
             "I find ways to overcome my challenges.", "I make peace with what I can’t control.",
             "I choose to be happy and completely love myself today and every day.",
             "I deserve happiness and success."]

        self_worth = ["I am good enough.", "I deserve joy.", "I am worthy of investing in myself.", "I deserve positivity.",
             "I am worthy of praise.", "I love myself.", "People like being around me.",
             "I have surpassed my own expectations in the past.", "I have innate value.", "My perspective matters.",
             "I respect myself.", "I have meaning.", "I am purposeful.", "I am unique", "I am interesting.",
             "I am deliberate.", "I am intentional.", "I am wise.", "I am respected.",
             "I matter to the world.", "I am doing my best.", "I deserve support from those who are close to me",
             "I am complete as I am.", "I am allowed to feel good.", "My past will never define me.",
             "I am breaking generational cycles", "I am abandoning bad habits.", "I am proud of myself.",
             "I am advancing at my own pace.", "There are a million reasons to be proud of myself.",
             "My ancestors would be proud of me."]

        worry_stress_negative_feelings = ["I easily release all tension from my mind and body.",
                                                        " I am beginning to live a more balanced and peaceful life.",
                                                        "Every day I become more peaceful and content.",
                                                        "My mind is becoming calm and clear.",
                                                        "I am working calmly towards resolving my worries and concerns.",
                                                        "I easily meet and overcome challenges.",
                                                        "I release my fear of failure. I am motivated by love, always.",
                                                        "I am grounded, centered, and stable.",
                                                        "I am safe and supported.",
                                                        "I am equipped with all the resources I need to walk through this experience with courage and strength.",
                                                        "I have everything I need to overcome any obstacles that come my way.",
                                                        "I will not worry about things I cannot control.",
                                                        "I focus on what I can control and let go of what I cannot.",
                                                        "I have the power to overcome my doubts, worries, and fears.",
                                                        "I own my power and recognize the strength inside me.",
                                                        "It’s okay for me to feel stressed. I respond to my stress with love and compassion",
                                                        "I allow myself to take things one moment at a time.",
                                                        "I am in charge of my own energy. I’m the only one who chooses how I feel.",
                                                        "I have the power to control my emotions.",
                                                        "I choose to think positive thoughts.",
                                                        "I am strong, capable, and resilient.",
                                                        "I am far stronger than I realize.",
                                                        "I am capable of handling anything that comes my way.",
                                                        "Calm is my superpower.",
                                                        "I am resilient. Nothing can shake me.",
                                                        "I release worst case scenario thinking.",
                                                        "I free myself from fear of the unknown",
                                                        "I am kind and compassionate toward myself when I make a mistake.",
                                                        "Mistakes do not equal failure.",
                                                        "Mistakes do not define me. I am allowed the grace of imperfection.",
                                                        "I choose to view adversity as an opportunity for growth.",
                                                        "I have the power to make profound positive changes.",
                                                        "I rise in the face of new challenges.",
                                                        "When I’m feeling overwhelmed, I allow myself to step back and breathe.",
                                                        "My peace is more important.",
                                                        "I inhale peace and exhale worry.",
                                                        "This feeling is temporary.",
                                                        "I am willing to view this experience through the eyes of love.",
                                                        "I choose peace over perfection.",
                                                        "I allow myself to feel all my emotions, but I have the ability to rise above anything that doesn’t serve my highest good.",
                                                        "I am worthy, no matter what I do or don’t accomplish today.",
                                                        "My worthiness is not defined by my achievements.",
                                                        "I choose courage over fear and peace over perfection.",
                                                        "I trust that the Universe gives me exactly what I need at exactly the right time.",
                                                        "My energy is not reserved for worrying. I use my energy to trust, believe, and have faith.",
                                                        "I cultivate deep courage and compassion within my mind, body, and spirit.",
                                                        "In this moment, I am exactly where I am meant to me.",
                                                        "The Universe supports me in every way.",
                                                        "I am living a fearless life.", "All is well.",
                                                        "All experiences shape me to be a stronger and braver version of myself."]

        greatness = ["I feel motivated and am moving in the direction of my dreams.",
                                   "I am motivated to continue perusing my goals.",
                                   " I feel alive, energized and motivated to take on any task in front of me.",
                                   "I am continually re-energized and share that enthusiasm with others.",
                                   "Because of my profound energy, I achieve and exceed at all that I do.",
                                   "I am so motivated that others get inspired just by being around me.",
                                   "I am confident in what I do and that keeps me motivated to continue moving forward.",
                                   "I am motivated and live my life to the fullest.",
                                   "I go confidently in the direction of my goals.",
                                   "I see lessons where others see problems.",
                                   "My goals keep me motivated, focused and driven.",
                                   "I like having something to look forward to.",
                                   "I am great at manifesting good things for myself.",
                                   "I am great at helping people around me grow."]

        focus_work_career = ["Right now, I am working at my dream job.",
                                           "I am a valued person at my workplace and my voice is always heard respectfully.",
                                           "I have a great relationship with my colleagues as well as my boss.",
                                           "I am a born entrepreneur. I recognize and seize opportunities as and when they appear.",
                                           "I engage in work that impacts this world positively.",
                                           "I am creating the career of my dreams. It appears in my mind and then in my world.",
                                           "As I align my career with my true talents, the money and the happiness flows to me!",
                                           "I wake up today feeling calm, centered, and grounded.",
                                           "I am strong, confident, and empowered.",
                                           "I am capable and equipped to handle anything that comes my way today.",
                                           "I am equipped with all the tools I need to succeed.",
                                           "I inhale positive energy and exhale my worries.",
                                           "I make the best and most out of everything that comes my way.",
                                           "I am in charge of my own energy. I’m the only one who chooses how I feel.",
                                           "Today, I choose to feel calm, grounded, peaceful, and secure.",
                                           "I can accomplish anything I focus on.",
                                           "I am committed, focused, and persistent.",
                                           "I am worthy of being praised and rewarded for my efforts.",
                                           "I am worthy of unconditional respect and acceptance.",
                                           "My presence is welcomed and appreciated by others.",
                                           "I choose to give my smile freely and spread joy to others.",
                                           "I am surrounded by uplifting, supportive people who believe in me.",
                                           "I lovingly lift up my coworkers and never put them down.",
                                           "I am able to ask for and accept help when I need it.",
                                           "My contributions are meaningful, valued, and rewarded.",
                                           "I am courageous and stand up for myself.",
                                           "I am superior to negative thoughts and low actions.",
                                           "I am able to release negative thoughts and feelings that do not serve me.",
                                           "I let go of worries that drain my energy.",
                                           "Instead of focusing on what’s going wrong, I focus my energy on what’s going right.",
                                           "External forces cannot dampen my resilient spirit.",
                                           "I am kind and compassionate toward myself when I make a mistake.",
                                           "Mistakes do not equal failure.",
                                           "Mistakes do not define me. I am allowed the grace of imperfection.",
                                           "I choose to view adversity as an opportunity for growth.",
                                           "There is a benefit and opportunity in every experience I have.",
                                           "I am willing to believe that things will always work out, even when they don’t feel like it.",
                                           "I cannot always control my external world, but I can control my reactions to it.",
                                           "I am equipped with all the tools I need to walk through this day with dignity and grace.",
                                           "I am willing to learn, grow, and continuously evolve.",
                                           "My ability to conquer challenges is limitless. My ability to succeed is infinite.",
                                           "Everything I do today is enough. (And so am I.)",
                                           "I am allowed to take breaks.",
                                           "I am worthy of being paid highly for my time, skills, and effort.",
                                           "My talents are worthy of being paid abundantly.",
                                           "I am grateful for a job that provides me with a consistent income.",
                                           "I am grateful for a job that provides me with opportunities to learn and grow.",
                                           "I am proud of my efforts.", "I am confident I can reach any goal.",
                                           "I can do hard things.", "I rise in the face of new challenges.",
                                           "I rise in the face of new challenges.",
                                           "I rise in the face of new challenges.",
                                           "All I can do is offer my best self. That is always enough.",
                                           "No matter what happens today, I choose to remain aligned with my highest self."]

        search = self.search_affirmation_dialog.content_cls.ids.affirmation_search_input.text
        self.search_affirmation_dialog.content_cls.ids.affirmation_search_input.text = ""
        if search.lower() == 'man':
            self.show_loading_dialog()
            self.check_for_network()
            for i in range(20):
                self.root.ids.affirmation_layout.add_widget(
                     DilayAffirmationCard(affirmation_text=random.choice(man), affirmation_image=random.choice(affirmation_bg_image)))
                toast(f"20 free Affirmation have been added on {search}")
                self.root.ids.affirm_text.text = f"20 free Affirmation have been added on {search}"

        elif search.lower() == 'men':
            self.show_loading_dialog()
            self.check_for_network()
            for i in range(20):
                self.root.ids.affirmation_layout.add_widget(
                    DilayAffirmationCard(affirmation_text=random.choice(man),
                                         affirmation_image=random.choice(affirmation_bg_image)))
                toast(f"20 free Affirmation have been added on {search}")
                self.root.ids.affirm_text.text = f"20 free Affirmation have been added on {search}"
        elif search.lower() == 'self worth':
            self.show_loading_dialog()
            self.check_for_network()
            for i in range(30):
                self.root.ids.affirmation_layout.add_widget(
                    DilayAffirmationCard(affirmation_text=random.choice(self_worth),
                                         affirmation_image=random.choice(affirmation_bg_image)))
                toast(f"30 free Affirmation have been added on {search}")
                self.root.ids.affirm_text.text = f"30 free Affirmation have been added on {search}"
        elif search.lower() == 'relationship':
            self.show_loading_dialog()
            self.check_for_network()
            for i in range(40):
                self.root.ids.affirmation_layout.add_widget(
                    DilayAffirmationCard(affirmation_text=random.choice(relationship),
                                         affirmation_image=random.choice(affirmation_bg_image)))
                toast(f"40 free Affirmation have been added on {search}")
                self.root.ids.affirm_text.text = f"40 free Affirmation have been added on {search}"
        elif search.lower() == 'woman':
            self.show_loading_dialog()
            self.check_for_network()
            for i in range(40):
                self.root.ids.affirmation_layout.add_widget(
                    DilayAffirmationCard(affirmation_text=random.choice(women),
                                         affirmation_image=random.choice(affirmation_bg_image)))
                toast(f"35 free Affirmation have been added on {search}")
                self.root.ids.affirm_text.text = f"35 free Affirmation have been added on {search}"
        elif search.lower() == 'women':
            self.show_loading_dialog()
            self.check_for_network()
            for i in range(35):
                self.root.ids.affirmation_layout.add_widget(
                    DilayAffirmationCard(affirmation_text=random.choice(women),
                                         affirmation_image=random.choice(affirmation_bg_image)))
                toast(f"35 free Affirmation have been added on {search}")
                self.root.ids.affirm_text.text = f"35 free Affirmation have been added on {search}"
        elif search.lower() == 'success':
            self.show_loading_dialog()
            self.check_for_network()
            for i in range(50):
                self.root.ids.affirmation_layout.add_widget(
                    DilayAffirmationCard(affirmation_text=random.choice(success),
                                         affirmation_image=random.choice(affirmation_bg_image)))
                toast(f"50 free Affirmation have been added on {search}")
                self.root.ids.affirm_text.text = f"50 free Affirmation have been added on {search}"
        elif search.lower() == 'hope':
            self.show_loading_dialog()
            self.check_for_network()
            for i in range(50):
                self.root.ids.affirmation_layout.add_widget(
                    DilayAffirmationCard(affirmation_text=random.choice(hope_confidence_positive_happiness),
                                         affirmation_image=random.choice(affirmation_bg_image)))
                toast(f"50 free Affirmation have been added on {search}")
                self.root.ids.affirm_text.text = f"50 free Affirmation have been added on {search}"
        elif search.lower() == 'confidence':
            self.show_loading_dialog()
            self.check_for_network()
            for i in range(50):
                self.root.ids.affirmation_layout.add_widget(
                    DilayAffirmationCard(affirmation_text=random.choice(hope_confidence_positive_happiness),
                                         affirmation_image=random.choice(affirmation_bg_image)))
                toast(f"50 free Affirmation have been added on {search}")
                self.root.ids.affirm_text.text = f"50 free Affirmation have been added on {search}"
        elif search.lower() == 'positive':
            self.show_loading_dialog()
            self.check_for_network()
            for i in range(50):
                self.root.ids.affirmation_layout.add_widget(
                    DilayAffirmationCard(affirmation_text=random.choice(hope_confidence_positive_happiness),
                                         affirmation_image=random.choice(affirmation_bg_image)))
                toast(f"50 free Affirmation have been added on {search}")
                self.root.ids.affirm_text.text = f"50 free Affirmation have been added on {search}"
        elif search.lower() == 'happiness':
            self.show_loading_dialog()
            self.check_for_network()
            for i in range(50):
                self.root.ids.affirmation_layout.add_widget(
                    DilayAffirmationCard(affirmation_text=random.choice(hope_confidence_positive_happiness),
                                         affirmation_image=random.choice(affirmation_bg_image)))
                toast(f"50 free Affirmation have been added on {search}")
                self.root.ids.affirm_text.text = f"50 free Affirmation have been added on {search}"
        elif search.lower() == 'worry':
            self.show_loading_dialog()
            self.check_for_network()
            for i in range(50):
                self.root.ids.affirmation_layout.add_widget(
                    DilayAffirmationCard(affirmation_text=random.choice(worry_stress_negative_feelings),
                                         affirmation_image=random.choice(affirmation_bg_image)))
                toast(f"50 free Affirmation have been added on {search}")
                self.root.ids.affirm_text.text = f"50 free Affirmation have been added on {search}"
        elif search.lower() == 'stress':
            self.show_loading_dialog()
            self.check_for_network()
            for i in range(50):
                self.root.ids.affirmation_layout.add_widget(
                    DilayAffirmationCard(affirmation_text=random.choice(worry_stress_negative_feelings),
                                         affirmation_image=random.choice(affirmation_bg_image)))
                toast(f"50 free Affirmation have been added on {search}")
                self.root.ids.affirm_text.text = f"50 free Affirmation have been added on {search}"
        elif search.lower() == 'negative':
            self.show_loading_dialog()
            self.check_for_network()
            for i in range(50):
                self.root.ids.affirmation_layout.add_widget(
                    DilayAffirmationCard(affirmation_text=random.choice(worry_stress_negative_feelings),
                                         affirmation_image=random.choice(affirmation_bg_image)))
                toast(f"50 free Affirmation have been added on {search}")
                self.root.ids.affirm_text.text = f"50 free Affirmation have been added on {search}"
        elif search.lower() == 'feelings':
            self.show_loading_dialog()
            self.check_for_network()
            for i in range(50):
                self.root.ids.affirmation_layout.add_widget(
                    DilayAffirmationCard(affirmation_text=random.choice(worry_stress_negative_feelings),
                                         affirmation_image=random.choice(affirmation_bg_image)))
                toast(f"50 free Affirmation have been added on {search}")
                self.root.ids.affirm_text.text = f"50 free Affirmation have been added on {search}"
        elif search.lower() == 'greatness':
            self.show_loading_dialog()
            self.check_for_network()
            for i in range(50):
                self.root.ids.affirmation_layout.add_widget(
                    DilayAffirmationCard(affirmation_text=random.choice(greatness),
                                         affirmation_image=random.choice(affirmation_bg_image)))
                toast(f"40 free Affirmation have been added on {search}")
                self.root.ids.affirm_text.text = f"40 free Affirmation have been added on {search}"
        elif search.lower() == 'focus':
            self.show_loading_dialog()
            self.check_for_network()
            for i in range(50):
                self.root.ids.affirmation_layout.add_widget(
                    DilayAffirmationCard(affirmation_text=random.choice(focus_work_career),
                                         affirmation_image=random.choice(affirmation_bg_image)))
                toast(f"50 free Affirmation have been added on {search}")
                self.root.ids.affirm_text.text = f"50 free Affirmation have been added on {search}"
        elif search.lower() == 'work':
            self.show_loading_dialog()
            self.check_for_network()
            for i in range(50):
                self.root.ids.affirmation_layout.add_widget(
                    DilayAffirmationCard(affirmation_text=random.choice(focus_work_career),
                                         affirmation_image=random.choice(affirmation_bg_image)))
                toast(f"50 free Affirmation have been added on {search}")
                self.root.ids.affirm_text.text = f"50 free Affirmation have been added on {search}"
        elif search.lower() == 'career':
            self.show_loading_dialog()
            self.check_for_network()
            for i in range(50):
                self.root.ids.affirmation_layout.add_widget(
                    DilayAffirmationCard(affirmation_text=random.choice(focus_work_career),
                                         affirmation_image=random.choice(affirmation_bg_image)))
                toast(f"50 free Affirmation have been added on {search}")
                self.root.ids.affirm_text.text = f"50 free Affirmation have been added on {search}"
        elif search.lower() == ' ':
            self.show_loading_dialog()
            self.check_for_network()
            toast(f"Your search is Empty try searching for something")
            self.root.ids.affirm_text.text = " "

        elif search.lower() == '':
            self.show_loading_dialog()
            self.check_for_network()
            self.root.ids.affirm_text.text = ""
            toast(f"Your search is Empty try searching for something", background=self.theme_cls.primary_color, duration=4.5)
        else:
            toast(f"Sorry No result on {search} but 60 random affirmation was added", background=self.theme_cls.primary_color, duration=1.5)
            self.check_for_network()
            for i in range(60):
                self.get_affirmed()
        self.close_search_affirmation_dialog()

    def get_affirmed(self):
        #self.show_loading_dialog()
        affirmation_bg_image = random.choice(["motivation_images/accessories.jpg","motivation_images/motivation_image4.jpg","motivation_images/motivation_image5.jpg","motivation_images/motiv3.jpg","motivation_images/motiv2.jpg","motivation_images/motivation_image3.jpg","motivation_images/motiv2.jpg","motivation_images/motivation_image7.jpg", "motivation_images/motivation_image8.jpg", "motivation_images/motivation_image9.jpg", "motivation_images/motivation_image10.jpg","motivation_images/motivation_image11.jpg",
                                              "motivation_images/motivation_image13.jpg","motivation_images/motivation_image14.jpg", "motivation_images/motivation_image15.jpg","motivation_images/motivation_image16.jpg", "motivation_images/motivation_image17.jpg", "motivation_images/motivation_image18.jpg", "motivation_images/motivation_image19.jpg", "motivation_images/motivation_image21.jpg", "motivation_images/motivation_image22.jpg", "motivation_images/motivation_image23.jpg",
                                              "motivation_images/motivation_image24.jpg", "motivation_images/motivation_image25.jpg","motivation_images/motivation_image29.jpg",])
        affirm = random.choice(["I am positive. I am loved. I am enough.", " am perfectly healthy, my body is in great shape, and I am beaming with energy.", "I am enjoying an abundance of energy and I am feeling so healthy both physically and mentally",
                  " I release myself from all negative energy and align myself with pure, fun, and positive energy.", "Every day in every way, I am getting healthier and healthier, and feeling better and better.",
                  "I love myself and I am perfectly healthy in every way possible.", "I always feel good and as a result, my body feels good and I radiate good feelings.", "Good health is my birth right. I bless my body every single day and take good care of it.",
                  "I have a strong heart and a steel body. I am vigorous, energetic, and full of vitality.", "I treat my body as a temple. It is holy, it is clean and it is full of goodness.", "I breathe deeply, exercise regularly and feed only good nutritious food to my body.",
                  "I will be at ease and enjoy the simple moments.", "Money comes to me in expected and unexpected ways.", "I know who I am and I know what I deserve.", "I know who I am and I know what I deserve.", "I am allowed to say no to others and yes to myself.", "I am open to new experiences and new things.", "I make peace with my past and I am ready to receive the good that comes my way.", "I am proud of who I am and all that I have and will accomplish.",
                  "I am learning valuable lessons from myself every day", "I am beautiful and I love all aspects of me and who I am.", "I am unaffected by the judgment of others.", "I am stronger than my excuses.", "I am stronger than my excuses.", "I am confident in my ability to …..", "My drive and ambition allow me to achieve my goals.", "It’s okay to make mistakes. I learn from my mistakes. Mistakes are a chance to grow.",
                  "When I need help, I will ask for it, I won’t be afraid of others judging me.", "I am responsible for my actions.", "I am going to train my brain to do it.", "I am thankful for all I have and all I will accomplish.", "My past does not define my future.", "I am talented and intelligent. My possibilities are endless.", "“I forgive myself for having a bad day.", "I am proud of who I am and excited about who I will be.",
                  "Today I let go of anything that doesn’t add to my happiness and goals.", "I have the power to create the life I desire.", "I have the power to create the life I desire.", "I love being me.", "I am worthy of love and happiness.", "I take action towards my goals every day.", "I don’t fail, I learn.", "I start every day with gratitude and thanks.", "Today is full of opportunity.",
                  "I am grateful for waking up today. I am grateful for what I have. I am grateful for being here.", "I am positive and create joy and happiness for others.", "I have a positive attitude and accept with an open heart everything that comes.", "I feel healthy, wealthy, and wise.", "I focus on what I can control. I let go of the rest."])

        self.root.ids.affirmation_layout.add_widget(
            DilayAffirmationCard(affirmation_text=affirm, affirmation_image=affirmation_bg_image))

    def save_users_details(self):
        database = sqlite3.connect('user_profile_details.db')
        curs = database.cursor()
        database.execute("CREATE TABLE if not exists user_detail(user_name,full_name text, email text, password text, skills text)")
        database.commit()
        database.close()

    def add_update_user_details(self):
        self.user_store = JsonStore('user_details.json')
        self.user_store.put('tito', user_name=self.root.ids.username_textinput.text, full=self.root.ids.fullname_text_field.text,
                  mail=self.root.ids.email_textfield.text, password=self.root.ids.password_text_field.text,
                  skills=self.root.ids.skills_textfield.text)
        self.show_user_details()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_keyboard=self.events)
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            preview=True
        )

    def file_manager_open(self):
        #if platform == 'android':
            #from android.permissions import request_permissions, Permission
            #request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])

        self.file_manager.show(primary_ext_storage)  # for mobile phone
        self.manager_open = True

    def select_path(self, path):
        '''It will be called when you click on the file name
        or the catalog selection button.

        :type path: str;
        :param path: path to the selected directory or file;
        '''

        self.exit_manager()
        toast(path)
        App.get_running_app().change_profile_source(path)

    def exit_manager(self, *args):
        '''Called when the user reaches the root of the directory tree.'''

        self.manager_open = False
        self.file_manager.close()

    def events(self, instance, keyboard, keycode, text, modifiers):
        '''Called when buttons are pressed on the mobile device.'''

        if keyboard in (1001, 27):
            if self.manager_open:
                self.file_manager.back()
        return True

    def change_profile_source(self, path):
        self.root.ids.profile.source = path # For mobile phone
        with open("profile_source.txt", "w") as f:
            f.write(path) # For mobile phone

        if os.path.isfile("profile_source.txt"):
            with open("profile_source.txt", "r") as f:
                some_path = f.read()
                if len(some_path) > 0:
                    self.root.ids.profile.source = some_path
                    self.root.ids.home_image.source = some_path
                    self.root.ids.weather_profile_image.source = some_path
                    self.root.ids.edit_profile_pics.source = some_path
                    self.root.ids.menu_profile_image.source = some_path
                else:
                    self.root.ids.profile.source = "store/cate-car.jpg"
                    self.root.ids.home_image.source = "store/moti.jfif"
                    self.root.ids.weather_profile_image.source = "store/propics2.jfif"
                    self.root.ids.edit_profile_pics.source = "store/profilepicsdemo1.jfif"
                    self.root.ids.menu_profile_image.source = "store/profilepicsdemo1.jfif"
        else:
            self.root.ids.profile.source = "store/cate-car.jpg"
            self.root.ids.home_image.source = "store/moti.jfif"
            self.root.ids.weather_profile_image.source = "store/propics2.jfif"
            self.root.ids.edit_profile_pics.source = "store/profilepicsdemo1.jfif"
            self.root.ids.menu_profile_image.source = "store/profilepicsdemo1.jfif"

    def reverse_color(self):
        self.root.ids.nav_icon5.color = rgba(200, 200, 200, 225)

    def __int__(self, **kwargs):
        super(XtrA, self).__init__(**kwargs)
        self.user_store = JsonStore('user_details.json')

    def hide_login_password(self):
        self.root.ids.login_password_btn.icon = "eye-off" if self.root.ids.login_password_btn.icon == "eye" else "eye"
        self.root.ids.login_password.password = False if self.root.ids.login_password.password is True else True

    def hide_password(self):
        self.root.ids.password_btn.icon = "eye-off" if self.root.ids.password_btn.icon == "eye" else "eye"
        if self.root.ids.password_btn.icon == "eye-off":
            self.root.ids.pass_word.text = "*" * len(str(self.root.ids.pass_word.text))
        else:
            self.root.ids.pass_word.text = self.user_store.get('tito')['password']

    def greet(self, *args):
        """Return part of day depending on time_now and the user's timzone
        offset value.

        user_tz_offset - integer of user's time zone offset in hours
        time_now - UTC time in seconds

        From  -  To  => part of day
        ---------------------------
        00:00 - 04:59 => midnight
        05:00 - 06:59 => dawn
        07:00 - 10:59 => morning
        11:00 - 12:59 => noon
        13:00 - 16:59 => afternoon
        17:00 - 18:59 => dusk
        19:00 - 20:59 => evening
        21:00 - 23:59 => night
        """
        #user_time = time_now + (user_tz_offset * 60 * 60)
        # gmtime[3] is tm_hour
        #user_hour = time.gmtime(user_time)[3]
        now = datetime.datetime.now()
        user_hour = now.hour
        if 0 <= user_hour < 5:
            self.root.ids.greeting.text = "It's MidNight"
            self.root.ids.welcome_text.text = "Still Awake? Get Affirmed & Motivated Tonight before You Sleep. and Perhaps set your Schedule for Tomorrow"
            self.root.ids.menu_image.source = "menuimages/image3.jpg"
        elif 5 <= user_hour < 7:
            self.root.ids.greeting.text = "It's Dawn"
            self.root.ids.welcome_text.text = "IT's Dawn!. Get Affirmed & Motivated Before its morning. and Perhaps set your Schedule for This Night & Tomorrow"
            self.root.ids.menu_image.source = "menuimages/morning_menu.png"
        elif 7 <= user_hour < 11:
            self.root.ids.greeting.text = 'Good Morning'
            self.root.ids.menu_image.source = "menuimages/morning_menu.png"
            self.root.ids.welcome_text.text = "Good Morning. This is the Best Time To Get Affirmed & Motivated during the day to keep you going. Then Perhaps set your Schedule for This Night & Tomorrow"
        elif 11 <= user_hour < 13:
            self.root.ids.greeting.text = "It's Noon"
            self.root.ids.menu_image.source = "menuimages/morning_menu.png"
            self.root.ids.welcome_text.text = "Hey it'Noon. Get Affirmed & Motivated to keep you going. and Perhaps set your Schedule for This Night & Tomorrow"
        elif 13 <= user_hour < 17:
            self.root.ids.greeting.text = 'Good Afternoon'
            self.root.ids.menu_image.source = "menuimages/morning_menu.png"
            self.root.ids.welcome_text.text = "Good Afternoon We know You are Tied. So Get Affirmed & Motivated this AfterNoon to keep you going. and Perhaps set your Schedule for This Night & Tomorrow"
        elif 19 <= user_hour < 21:
            self.root.ids.greeting.text = "Good Evening"
            self.root.ids.menu_image.source = "menuimages/image3.jpg"
            self.root.ids.welcome_text.text = "Good Evening, How are Feeling? Get Affirmed & Motivated This Evening before going to Bed. and Perhaps set your Schedule for Tomorrow"
        else:
            self.root.ids.greeting.text = "Good Night"
            self.root.ids.menu_image.source = "menuimages/image3.jpg"
            self.root.ids.welcome_text.text = "How Is The Night Going?. Get Affirmed & Motivated Tonight before going to Bed. and Perhaps set your Schedule for Tomorrow"

    def check_for_network(self, *args):
        try:
            url = "https://www.google.com"
            response = requests.get(url)
        except requests.ConnectionError:
            self.show_error_dialog()

    def check_login(self):
        if self.root.ids.user_name.text != '':
            self.root.ids.login_and_logout.text = "logout"
        else:
            self.root.ids.login_and_logout.text = "login"

    def color_normal(self):
        self.root.ids.navbar.md_bg_color = rgba(255, 255, 255, 255)
        self.root.ids.nav_icon1.text_color = self.theme_cls.primary_color
        self.root.ids.nav_icon2.text_color = rgba(200, 200, 200, 225)
        self.root.ids.nav_icon3.text_color = rgba(200, 200, 200, 225)
        self.root.ids.nav_icon4.text_color = rgba(200, 200, 200, 225)
        self.root.ids.nav_icon5.text_color = rgba(200, 200, 200, 225)

        self.root.ids.nav_icon1.disable = False
        self.root.ids.nav_icon2.disable = False
        self.root.ids.nav_icon3.disable = False
        self.root.ids.nav_icon4.disable = False
        self.root.ids.nav_icon5.disable = False

    def color_blank(self):
        self.root.ids.navbar.md_bg_color = rgba(0, 0, 0, 1)
        self.root.ids.nav_icon1.text_color = rgba(0, 0, 0, 1)
        self.root.ids.nav_icon2.text_color = rgba(0, 0, 0, 1)
        self.root.ids.nav_icon3.text_color = rgba(0, 0, 0, 1)
        self.root.ids.nav_icon4.text_color = rgba(0, 0, 0, 1)
        self.root.ids.nav_icon5.text_color = rgba(0, 0, 0, 1)

        self.root.ids.nav_icon1.disable = True
        self.root.ids.nav_icon2.disable = True
        self.root.ids.nav_icon3.disable = True
        self.root.ids.nav_icon4.disable = True
        self.root.ids.nav_icon5.disable = True

    def check_screen(self, *args):
        if self.root.ids.screen_manager.current == 'splash':
            self.color_blank()
        elif self.root.ids.screen_manager.current == 'login':
            self.color_blank()
            try:
                self.show_banner_ads()
            except:
                pass
            self.root.ids.login_back_btn.disabled = True
            self.root.ids.signup_back_btn.disabled = True
        elif self.root.ids.screen_manager.current == 'signup':
            self.color_blank()
            try:
                self.show_banner_ads()
            except:
                pass
            self.root.ids.login_back_btn.disabled = True
            self.root.ids.signup_back_btn.disabled = True

        else:
            self.color_normal()

    def change_color(self, instance):
        if instance in self.root.ids.values():
            current_id = list(self.root.ids.keys())[list(self.root.ids.values()).index(instance)]
            for i in range(5):
                if f"nav_icon{i + 1}" == current_id:
                    self.root.ids[f"nav_icon{i + 1}"].text_color = self.theme_cls.primary_color
                else:
                    self.root.ids[f"nav_icon{i + 1}"].text_color = rgba(200, 200, 200, 225)
        try:
            if self.root.ids.screen_manager == 'weather':
                self.show_interstitial_ads()
                self.show_banner_ads()
            elif self.root.ids.screen_manager == 'task':
                self.show_interstitial_ads()
                self.show_banner_ads()
            elif self.root.ids.screen_manager == 'home':
                self.show_interstitial_ads()
                self.show_banner_ads()
            elif self.root.ids.screen_manager == 'profile':
                self.show_interstitial_ads()
                self.show_banner_ads()
            elif self.root.ids.screen_manager == 'affirmation':
                self.show_interstitial_ads()
                self.show_banner_ads()
        except:
            pass

    def show_theme_picker(self):
        theme_dialog = MDThemePicker()
        theme_dialog.open()

    def print_theme(self):
        theme_connect = sqlite3.connect('myapp.db')
        theme_cursor = theme_connect.cursor()
        theme_cursor.execute("""SELECT * FROM theme ;""")
        current_theme = theme_cursor.fetchall()
        theme_connect.commit()

        if len(current_theme) == 0:
            theme_cursor.execute(
                """INSERT INTO theme (primary_palette, accent_palette, theme_style) VALUES (?, ?, ?);""",
                (self.theme_cls.primary_palette, self.theme_cls.accent_palette, self.theme_cls.theme_style))
            theme_connect.commit()
        else:
            theme_cursor.execute("""UPDATE theme SET primary_palette = ? , accent_palette = ? , theme_style = ? ;""", (
            self.theme_cls.primary_palette, self.theme_cls.accent_palette, self.theme_cls.theme_style))
            theme_connect.commit()

    def save_user_full_details(self):
        self.user_store.put('tito', user_name=self.root.ids.username_textinput.text,
                       full=self.root.ids.fullname_text_field.text,
                       mail=self.root.ids.email_textfield.text, password=self.root.ids.password_text_field.text,
                       skills=self.root.ids.skills_textfield.text)
        self.load_full_details()

    def load_full_details(self):
        self.root.ids.user_name.text = self.user_store.get('tito')['user_name']
        self.root.ids.fullname.text = self.user_store.get('tito')['full']
        self.root.ids.email.text = self.user_store.get('tito')['mail']
        self.root.ids.pass_word.text = self.user_store.get('tito')['password']
        self.root.ids.skills.text = self.user_store.get('tito')['skills']
        self.root.ids.home_user_name.text = self.user_store.get('tito')['user_name']

    def show_user_details(self):
        self.root.ids.signup_username.text = self.user_store.get('tito')['user_name']
        self.root.ids.signup_fullname.text = self.user_store.get('tito')['full']
        self.root.ids.signup_email.text = self.user_store.get('tito')['mail']
        self.root.ids.signup_password.text = self.user_store.get('tito')['password']
        self.root.ids.signup_skills.text = self.user_store.get('tito')['skills']
        self.root.ids.home_user_name.text = self.user_store.get('tito')['user_name']

    # this is the signup function
    def send_signup_data(self, signup_email, signup_password):
        signup_username = self.root.ids.signup_username.text
        signup_fullname = self.root.ids.signup_fullname.text
        signup_email1 = self.root.ids.signup_email.text
        signup_password1 = self.root.ids.signup_password.text
        signup_skills = self.root.ids.signup_skills.text
        self.show_loading_dialog()
        try:
            city_name = "abuja"  # self.search_weather_dialog.content_cls.ids.weather_search_input.text
            API_KEY = '94cd9f95c1140a8f35c5f6267b24b046'
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&units=metric&APPID={API_KEY}"
            req = requests.get(url)
            data = req.json()
            if data["cod"] != "404":
                if len(signup_fullname) > 3 and len(signup_username) and len(signup_email1) and len(signup_password1) and len(signup_skills):
                    self.user_store.put('tito', user_name=self.root.ids.signup_username.text,
                                        full=self.root.ids.signup_fullname.text,
                                        mail=self.root.ids.signup_email.text,
                                        password=self.root.ids.signup_password.text,
                                        skills=self.root.ids.signup_skills.text)
                    self.show_user_details()
                    screen_manager.transition.direction = "left"
                    self.root.ids.screen_manager.current = "login"
                    self.show_loading_dialog()
                    self.cursor.execute(f"insert into logindata values('{signup_email.text}', '{signup_password.text}')")
                    self.mydatabase.commit()
                    if re.fullmatch(self.regex, signup_email.text):
                        Clock.schedule_once(self.close_loading_dialog, 5)
                        self.root.ids.screen_manager.current = "login"
                    else:
                        Clock.schedule_once(self.close_loading_dialog, 5)
                        toast("Invalid Email")

                else:
                    Clock.schedule_once(self.close_loading_dialog, 5)
                    Snackbar(text="Please make sure all fields are filled and not empty ",
                             snackbar_x="10dp",
                             snackbar_y="10dp", size_hint_y=.08,
                             size_hint_x=(Window.width - (dp(10) * 2)) / Window.width, bg_color=(0, 179 / 255, 0, 1),
                             font_size="14sp").open()

            else:
                Clock.schedule_once(self.close_loading_dialog, 5)
                Snackbar(text="No Connection Please check your internet connection and Try again!", snackbar_x="10dp",
                         snackbar_y="10dp", size_hint_y=.08,
                         size_hint_x=(Window.width - (dp(10) * 2)) / Window.width, bg_color=(0, 179 / 255, 0, 1),
                         font_size="14sp").open()
        except requests.ConnectionError:
            self.close_loading_dialog()
            self.show_error_dialog()

        except mysql.connector.errors.IntegrityError:
            self.close_loading_dialog()
            Snackbar(text="email already exist try another email", snackbar_x="10dp",
                     snackbar_y="10dp", size_hint_y=.08,
                     size_hint_x=(Window.width - (dp(10) * 2)) / Window.width, bg_color=(0, 179 / 255, 0, 1),
                     font_size="14sp").open()

    # this is the login in function
    def retrieve_and_validate(self, login_email, login_password):
        try:
            self.show_loading_dialog()
            city_name = "abuja"  # self.search_weather_dialog.content_cls.ids.weather_search_input.text
            API_KEY = '94cd9f95c1140a8f35c5f6267b24b046'
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&units=metric&APPID={API_KEY}"
            req = requests.get(url)
            data = req.json()
            if data["cod"] != "404":
                self.show_loading_dialog()
                self.cursor.execute("select * from logindata")
                email_list = []
                for i in self.cursor.fetchall():
                    email_list.append(i[0])
                if login_email.text in email_list and login_email.text != "":
                    self.cursor.execute(f"select password from logindata where emai='{login_email.text}'")
                    for j in self.cursor:
                        if login_password.text == j[0]:
                            Clock.schedule_once(self.close_loading_dialog, 3)
                            Snackbar(text="Login Successfully",
                                     snackbar_x="10dp",
                                     snackbar_y="10dp", size_hint_y=.08,
                                     size_hint_x=(Window.width - (dp(10) * 2)) / Window.width,
                                     bg_color=(0, 179 / 255, 0, 1),
                                     font_size="14sp").open()

                            self.root.ids.screen_manager.current = "menu"
                            self.show_user_details()
                        else:
                            Clock.schedule_once(self.close_loading_dialog, 3)
                            Snackbar(text="Incorrect Password",
                                     snackbar_x="10dp",
                                     snackbar_y="10dp", size_hint_y=.08,
                                     size_hint_x=(Window.width - (dp(10) * 2)) / Window.width,
                                     bg_color=(0, 179 / 255, 0, 1),
                                     font_size="14sp").open()

                else:
                    Clock.schedule_once(self.close_loading_dialog, 3)
                    Snackbar(text="Incorrect Email",
                             snackbar_x="10dp",
                             snackbar_y="10dp", size_hint_y=.08,
                             size_hint_x=(Window.width - (dp(10) * 2)) / Window.width, bg_color=(0, 179 / 255, 0, 1),
                             font_size="14sp").open()

            else:
                Clock.schedule_once(self.close_loading_dialog, 3)
                Snackbar(text="No Connection Please check your internet connection and Try again!", snackbar_x="10dp",
                         snackbar_y="10dp", size_hint_y=.08,
                         size_hint_x=(Window.width - (dp(10) * 2)) / Window.width, bg_color=(0, 179 / 255, 0, 1),
                         font_size="14sp").open()
        except requests.ConnectionError:
            Clock.schedule_once(self.close_loading_dialog, 3)
            self.show_error_dialog()

        except mysql.connector.errors.IntegrityError:
            Clock.schedule_once(self.close_loading_dialog, 3)
            Snackbar(text="We are having an error Storing this password please enter a different one thanks.", snackbar_x="10dp",
                     snackbar_y="10dp", size_hint_y=.08,
                     size_hint_x=(Window.width - (dp(10) * 2)) / Window.width, bg_color=(0, 179 / 255, 0, 1),
                     font_size="14sp").open()
        #self.close_loading_dialog()

    def show_banner_ads(self, *args):
        self.ads.show_banner()

    def show_interstitial_ads(self, *args):
        self.ads.show_interstitial()

    def on_start(self):
        self.check_screen()
        Clock.schedule_once(self.show_loading_dialog, 18)
        Clock.schedule_once(self.menu, 13)
        Clock.schedule_once(self.check_screen, 15)
        theme_connect = sqlite3.connect('myapp.db')
        theme_cursor = theme_connect.cursor()
        theme_cursor.execute("""SELECT * FROM theme ;""")
        current_theme = theme_cursor.fetchall()
        theme_connect.commit()
        theme_connect.close()
        self.root.ids.login_back_btn.disabled = True
        self.root.ids.signup_back_btn.disabled = True
        # [('Purple', 'BlueGray', 'Light')]
        Clock.schedule_once(self.check_for_network, 30)
        Clock.schedule_once(self.close_loading_dialog, 35)
        if len(current_theme) == 0:
            self.theme_cls.primary_palette = 'BlueGray'
            self.theme_cls.accent_palette = "BlueGray"
            self.theme_cls.primary_hue = "500"
            self.theme_cls.theme_style = "Light"
        else:
            self.theme_cls.primary_palette = current_theme[0][0]
            self.theme_cls.accent_palette = current_theme[0][1]
            self.theme_cls.primary_hue = "500"
            self.theme_cls.theme_style = current_theme[0][2]
        self.check_screen()
        try:
            if os.path.isfile("profile_source.txt"):
                with open("profile_source.txt", "r") as f:
                    some_path = f.read()
                    if len(some_path) > 0:
                        self.root.ids.profile.source = some_path
                        self.root.ids.home_image.source = some_path
                        self.root.ids.weather_profile_image.source = some_path
                        self.root.ids.edit_profile_pics.source = some_path
                        self.root.ids.menu_profile_image.source = some_path
                    else:
                        self.root.ids.profile.source = "store/cate-car.jpg"
                        self.root.ids.home_image.source = "store/moti.jfif"
                        self.root.ids.weather_profile_image.source = "store/propics2.jfif"
                        self.root.ids.edit_profile_pics.source = "store/profilepicsdemo1.jfif"
                        self.root.ids.menu_profile_image.source = "store/profilepicsdemo1.jfif"
            else:
                self.root.ids.profile.source = "store/cate-car.jpg"
                self.root.ids.home_image.source = "store/moti.jfif"
                self.root.ids.weather_profile_image.source = "store/propics2.jfif"
                self.root.ids.edit_profile_pics.source = "store/profilepicsdemo1.jfif"
                self.root.ids.menu_profile_image.source = "store/profilepicsdemo1.jfif"

            #self.save_users_details()
        except:
            self.root.ids.menu_profile_image.source = some_path
            pass

        try:
            self.show_tasks_progress()
            self.show_user_details()
            self.load_full_details()
            self.root.ids.pass_word.text = "*" * len(str(self.root.ids.pass_word.text))
        except:
            pass

        self.greet()
        Clock.schedule_interval(self.greet, 50)
        Clock.schedule_interval(self.check_for_network, 75)
        Clock.schedule_once(self.load, 20)
        #self.auto_get_weather_and_location()
        #self.get_affirmed()

        today = datetime.date.today()
        wd = datetime.date.weekday(today)
        days = ["Mon", "Tues", "Wed", "Thurs", "Fri", "Sat", "Sun"]
        year = str(datetime.datetime.now().year)
        month = str(datetime.datetime.now().strftime("%b"))
        day = str(datetime.datetime.now().strftime("%d"))
        self.root.ids.date.text = f"Get Motivated Today  {days[wd]}, {day}, {month}, {year}"
        self.root.ids.menu_date.text = f"Today {days[wd]}, {day}, {month}, {year}"
        for i in range(30):
            self.get_affirmed()
        #if self.root.ids.screen_manager.current is 'menu':

        try:
            completed_tasks, uncomplete_tasks = db.get_tasks()

            if uncomplete_tasks != []:
                for task in uncomplete_tasks:
                    add_task = ListItemWithCheckbox(pk=task[0], text=task[1], secondary_text=task[2], md_bg_color=rgba(randrange(255), randrange(255), randrange(255), 255))
                    self.root.ids.container.add_widget(add_task)

            if completed_tasks != []:
                for task in completed_tasks:
                    add_task = ListItemWithCheckbox(pk=task[0], text='[s]' + task[1] + '[/s]', secondary_text=task[2], md_bg_color=rgba(randrange(255), randrange(255), randrange(255), 255))
                    add_task.ids.check.active = True

        except Exception as e:
            pass

    def menu(self, *args):
        self.root.ids.screen_manager.current = 'menu'

    def load(self, *args):
        try:
            self.show_banner_ads()
            for i in range(30):
                self.quotes_for_the_day()
            for i in range(30):
                self.most_popular_quote()
            for i in range(3):
                self.get_my_quotes()
            # to add 20 different quotes of the day we use the range function
            for i in range(30):
                self.get_quotes_of_the_day()
            # Load the saved tasks and add them to the MDList widget when the application start

        except requests.exceptions.ConnectionError:
            self.show_error_dialog()

    def on_complete2(self, checkbox, value, male_button, calculate_btn):

        if value:
            #status.text = "Completed"

            calculate_btn.disabled = False
            calculate_btn.md_bg_color = self.theme_cls.primary_color

            male_button.theme_text_color = "Custom"
            male_button.text_color = self.theme_cls.accent_color

        else:
            male_button.text_color = rgba(180, 180, 180, 255)
            calculate_btn.disabled = True
            #calculate_btn.disabled = True
            #toast("please choose your gender by clicking on the checkbox of the gender that suits your gender ")

    def on_complete1(self, checkbox, value, female_button, calculate_btn):
        if value:
            calculate_btn.disabled = False
            calculate_btn.md_bg_color = self.theme_cls.primary_color
            female_button.theme_text_color = "Custom"
            female_button.text_color = self.theme_cls.accent_color
        else:
            female_button.text_color = rgba(180, 180, 180, 255)
            calculate_btn.disabled = True

    def get_height_value(self):
        slider_value = self.root.ids.height_value
        self.root.ids.slider_text.text = str(int(slider_value.value))

    # function to control the weight selection of the user
    def increase_weight(self):
        self.weight = self.weight + 1

    def decrease_weight(self):
        self.weight = self.weight - 1

    # function to control the age  selection of the user
    def increase_age(self):
        self.age = self.age + 1

    def decrease_age(self):
        self.age = self.age - 1

    # function to calculate the BMI
    def calculate_bmi(self):
        height = (self.root.ids.height_value.value) / 100
        height_squared = height * height
        bmi = self.weight / height_squared
        weight_range = 'normal'
        if bmi < 18.5:
            weight_range = 'UnderWeight'
        elif bmi >= 18.5 and bmi <= 24.9:
            weight_range = 'normal'
        elif bmi >= 25 and bmi <= 29.9:
            weight_range = 'Overweight'
        elif bmi > 30:
            weight_range = 'Obese'
        self.dailog = MDDialog(title='BMI Calculated', text=f'your BMI is {bmi} \nYour Category is {weight_range}',buttons=[
                        MDFlatButton(
                            text="CANCEL", on_release=self.close_bmi_dailog
                        ),

                        MDFlatButton(
                            text="watch weight?", theme_text_color="Custom", text_color=self.theme_cls.accent_color
                        ),
                    ],
                )
        self.dailog.open()

    def close_bmi_dailog(self, obj):
        self.dailog.dismiss()

    def show_delete_task_dialog(self):
        if not self.delete_task_dialog:
            self.delete_task_dialog = MDDialog(
                title="Delete Alart!",
                type="custom",
                content_cls=Content_delete_dialog(),
                md_bg_color=rgba(randrange(255), randrange(255), randrange(255), 255)

            )
        self.delete_task_dialog.open()

    def close_delete_task_dialog(self, *args):
        self.delete_task_dialog.dismiss()

    def __delete__(self, instance):
        self.delete_task_dialog.content_cls.remove_widget(ListItemWithCheckbox(self))

    def show_advice_dialog(self):
        if not self.advice_dialog:
            self.advice_dialog = MDDialog(
                title="Advice Based On Weather ",
                type="custom",
                radius=[20],
                content_cls=AdviceContent(),
            )

        self.advice_dialog.open()

    def close_advice_dialog(self):
        self.advice_dialog.dismiss()

    def add_task(self, task, task_date):
        '''Add task to the list of tasks'''

        # Add task to the db
        created_task = db.create_task(task.text, task_date)  # Here
        toast("Successfully Created: " + task.text, background=self.theme_cls.primary_color)
        self.root.ids.container.add_widget(
            ListItemWithCheckbox(pk=created_task[0], text='[b]' + created_task[1] + '[/b]',
                                 secondary_text=created_task[2], md_bg_color=rgba(randrange(255), randrange(255), randrange(255), 255)))  # Here
        task.text = '' # set the dialog entry to an empty string(clear the text entry)

    def show_task_dialog(self):
        if not self.task_list_dialog:
            self.task_list_dialog = MDDialog(
                title="Create Task",
                type="custom",
                content_cls=DialogContent(),
            )

        self.task_list_dialog.open()

    def close_dialog(self, *args):
        self.task_list_dialog.dismiss()

    def textfeild_icon_color_change(self):
        if len(self.home_search_dialog.content_cls.ids.motivation_search_input.text) > 2:
            self.home_search_dialog.content_cls.ids.search_icon.text_color = self.theme_cls.primary_color

        else:
            self.home_search_dialog.content_cls.ids.search_icon.text_color = rgba(180, 180, 180, 225)

    def show_weather_search_dialog(self):
        if not self.search_weather_dialog:
            self.search_weather_dialog = MDDialog(
                title="Search For Weather",
                type="custom",
                pos_hint={"center_y": .55},
                content_cls=WeatherSearchDialogContent(),
            )

        self.search_weather_dialog.open()

    def show_affirmation_search_dialog(self):
        if not self.search_affirmation_dialog:
            self.search_affirmation_dialog = MDDialog(
                title="Search For Affirmation",
                type="custom",
                pos_hint={"center_y": .55},
                content_cls=AffirmationSearchDialogContent(),
            )

        self.search_affirmation_dialog.open()

    def close_search_affirmation_dialog(self):
        self.search_affirmation_dialog.dismiss()

    def close_weather_search_dialog(self):
        self.search_weather_dialog.dismiss()

    def menu_color(self):
        self.root.ids.nav_icon1.theme_text_color = "Custom"
        self.root.ids.nav_icon1.text_color = rgba(200, 200, 200, 225)

    def auto_get_weather_and_location(self):

        try:
            url = 'http://ipinfo.io/json'
            url_response = urlopen(url)
            url_data = json.load(url_response)
            auto_weather_cityname = url_data['city']
            self.get_seven_days_weather(city_name=auto_weather_cityname)
            self.get_weather(city_name=auto_weather_cityname)

        except AttributeError:
            toast("error please try again")
        except requests.ConnectionError:
            toast("No Connection")

        except urllib.error.URLError:
            self.show_error_dialog()

    def get_seven_days_weather(self, city_name):
        api_key = "505f595a28b226541b72f07896f6ccda"

        try:
            url = f'https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}'
            request_weather = requests.get(url)
            respond = request_weather.json()
            lat = round(respond['coord']['lat'])
            lon = round(respond['coord']['lon'])

            url2 = f" http://api.openweathermap.org/data/2.5/forecast?q={city_name}&lat={lat}&lon={lon}&appid={api_key}"
            res = requests.get(url2)
            data = res.json()

            url3 = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&units=metric&exclude=hourly&appid={api_key}"
            requst = requests.get(url3)
            json_data = requst.json()

            if respond["cod"] != "404":

                temp = json_data['current']['temp']
                description = json_data['current']['weather'][0]['description']


                # get the weather for the seven days
                day1_morn = int(json_data['daily'][1]['temp']['morn'])
                day1 = int(json_data['daily'][1]['temp']['day']) # [0]['description']
                day1_evening = int(json_data['daily'][1]['temp']['eve'])
                day1_night = int(json_data['daily'][1]['temp']['night'])
                # first_day_night = json_data['daily'][1]['weather'][0]['description']

                day2_morn = int(json_data['daily'][2]['temp']['morn'])
                day2 = int(json_data['daily'][2]['temp']['day'])
                day2_evening = int(json_data['daily'][2]['temp']['eve'])
                day2_night = int(json_data['daily'][2]['temp']['night'])

                day3_morn = int(json_data['daily'][3]['temp']['morn'])
                day3 = int(json_data['daily'][3]['temp']['day'])
                day3_evening = int(json_data['daily'][3]['temp']['eve'])
                day3_night = int(json_data['daily'][3]['temp']['night'])

                day4_morn = int(json_data['daily'][4]['temp']['morn'])
                day4 = int(json_data['daily'][4]['temp']['day'])
                day4_evening = int(json_data['daily'][4]['temp']['eve'])
                day4_night = int(json_data['daily'][4]['temp']['night'])

                day5_morn = int(json_data['daily'][5]['temp']['morn'])
                day5 = int(json_data['daily'][5]['temp']['day'])
                day5_evening = int(json_data['daily'][5]['temp']['eve'])
                day5_night = int(json_data['daily'][5]['temp']['night'])

                day6_morn = int(json_data['daily'][6]['temp']['morn'])
                day6 = int(json_data['daily'][6]['temp']['day'])
                day6_evening = int(json_data['daily'][6]['temp']['eve'])
                day6_night = int(json_data['daily'][6]['temp']['night'])

                day7_morn = int(json_data['daily'][7]['temp']['morn'])
                day7 = int(json_data['daily'][7]['temp']['day'])
                day7_evening = int(json_data['daily'][7]['temp']['eve'])
                day7_night = int(json_data['daily'][7]['temp']['night'])

                id = str(respond["weather"][0]["id"])

                # get the date for seven days
                first = datetime.datetime.now()
                self.root.ids.day1_date.text = first.strftime("%a")  # f"{day1_morn}°"  # 'Good Morning'
                second = first + datetime.timedelta(days=1)
                self.root.ids.day2_date.text = second.strftime("%a")  # f"{day2_morn}°"
                third = first + datetime.timedelta(days=2)
                self.root.ids.day3_date.text = third.strftime("%a")
                fourth = first + datetime.timedelta(days=3)
                self.root.ids.day4_date.text = fourth.strftime("%a")
                fifth = first + datetime.timedelta(days=4)
                self.root.ids.day5_date.text = fifth.strftime("%a")
                sixth = first + datetime.timedelta(days=5)
                self.root.ids.day6_date.text = sixth.strftime("%a")
                seventh = first + datetime.timedelta(days=6)
                self.root.ids.day7_date.text = seventh.strftime("%a")

                # get the 7days weather images

                firstday_image = json_data['daily'][0]['weather'][0]['icon']
                self.root.ids.day1_weather_image.source = f"7days_weather_imgs/{firstday_image}@2x.png"
                secondday_image = json_data['daily'][1]['weather'][0]['icon']
                self.root.ids.day2_weather_image.source = f"7days_weather_imgs/{secondday_image}@2x.png"
                thirdday_image = json_data['daily'][2]['weather'][0]['icon']
                self.root.ids.day3_weather_image.source = f"7days_weather_imgs/{thirdday_image}@2x.png"
                fourthday_image = json_data['daily'][3]['weather'][0]['icon']
                self.root.ids.day4_weather_image.source = f"7days_weather_imgs/{fourthday_image}@2x.png"
                fifthday_image = json_data['daily'][4]['weather'][0]['icon']
                self.root.ids.day5_weather_image.source = f"7days_weather_imgs/{fifthday_image}@2x.png"
                sixthday_image = json_data['daily'][5]['weather'][0]['icon']
                self.root.ids.day6_weather_image.source = f"7days_weather_imgs/{sixthday_image}@2x.png"
                seventhday_image = json_data['daily'][6]['weather'][0]['icon']
                self.root.ids.day7_weather_image.source = f"7days_weather_imgs/{seventhday_image}@2x.png"

                now = datetime.datetime.now()
                user_hour = now.hour

                if 7 <= user_hour < 11:
                    self.root.ids.day1_temperature.text = f"{day1_morn}°" #'Good Morning'
                    self.root.ids.day2_temperature.text = f"{day2_morn}°"
                    self.root.ids.day3_temperature.text = f"{day3_morn}°"
                    self.root.ids.day4_temperature.text = f"{day4_morn}°"
                    self.root.ids.day5_temperature.text = f"{day5_morn}°"
                    self.root.ids.day6_temperature.text = f"{day6_morn}°"
                    self.root.ids.day7_temperature.text = f"{day7_morn}°"

                elif 11 <= user_hour < 17:
                    self.root.ids.day1_temperature.text = f"{day1}°"  # 'Good Morning'
                    self.root.ids.day2_temperature.text = f"{day2}°"
                    self.root.ids.day3_temperature.text = f"{day3}°"
                    self.root.ids.day4_temperature.text = f"{day4}°"
                    self.root.ids.day5_temperature.text = f"{day5}°"
                    self.root.ids.day6_temperature.text = f"{day6}°"
                    self.root.ids.day7_temperature.text = f"{day7}°"
                elif 19 <= user_hour < 21:
                    self.root.ids.day1_temperature.text = f"{day1_evening}°"  # 'Good Morning'
                    self.root.ids.day2_temperature.text = f"{day2_evening}°"
                    self.root.ids.day3_temperature.text = f"{day3_evening}°"
                    self.root.ids.day4_temperature.text = f"{day4_evening}°"
                    self.root.ids.day5_temperature.text = f"{day5_evening}°"
                    self.root.ids.day6_temperature.text = f"{day6_evening}°"
                    self.root.ids.day7_temperature.text = f"{day7_evening}°"
                else:
                    self.root.ids.day1_temperature.text = f"{day1_night}°"  # 'Good Morning'
                    self.root.ids.day2_temperature.text = f"{day2_night}°"
                    self.root.ids.day3_temperature.text = f"{day3_night}°"
                    self.root.ids.day4_temperature.text = f"{day4_night}°"
                    self.root.ids.day5_temperature.text = f"{day5_night}°"
                    self.root.ids.day6_temperature.text = f"{day6_night}°"
                    self.root.ids.day7_temperature.text = f"{day7_night}°"

            else:
                pass

        except requests.ConnectionError:
            Snackbar(text="No Connection Please check your internet connection and check again!", snackbar_x="10dp",
                     snackbar_y="10dp", size_hint_y=.08,
                     size_hint_x=(Window.width - (dp(10) * 2)) / Window.width, bg_color=(0, 179 / 255, 0, 1),
                     font_size="14sp").open()

        except KeyError:
            Snackbar(text=f" '{city_name}' is not city or county name, you can't search for continent",
                     snackbar_x="11dp",
                     snackbar_y="10dp", size_hint_y=.1,
                     size_hint_x=(Window.width - (dp(10) * 3)) / Window.width, bg_color=(0, 179 / 255, 0, 1),
                     font_size="14sp").open()

    def get_weather(self, city_name):
        API_KEY = '94cd9f95c1140a8f35c5f6267b24b046'
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&units=metric&APPID={API_KEY}"
            response = requests.get(url)
            x = response.json()
            if x["cod"] != "404":
                self.show_loading_dialog()
                temperature = int(x["main"]["temp"])
                humidity = x["main"]["humidity"]
                pressure = x["main"]["pressure"]
                feels_like = x["main"]["feels_like"]
                temp_min = x["main"]["temp_min"]
                temp_max = x["main"]["temp_max"]
                weather = x["weather"][0]["main"]
                description = x["weather"][0]["description"]
                wind_speed = round(x["wind"]["speed"] * 18/5)
                visibility = x["visibility"]
                id = str(x["weather"][0]["id"])
                location = x["name"] + ", " + x["sys"]["country"]
                self.root.ids.temperature.text = f"{temperature}°"
                self.root.ids.weather.text = str(weather)
                self.root.ids.description.text = str(description)
                self.root.ids.humidity.text = f"{humidity}%"
                self.root.ids.pressure.text = f"{pressure}mbar"
                self.root.ids.wind_speed.text = f"{wind_speed}km/h"
                self.root.ids.visibility.text = f"Visibility:  {visibility} "
                self.root.ids.feels_like.text = f"Feels_like:  {feels_like}"
                self.root.ids.min_temp.text = f"Temp_min:  {temp_min}"
                self.root.ids.max_temp.text = f"Temp_max:  {temp_max}"
                self.root.ids.location.text = location
                # screen_manager.get_screen("weather2").ids.visibility.text = f"{visibility}mi"
                if id == "800":
                    self.root.ids.weather_image.source = "weather/clearsky.png"
                    Clock.schedule_once(self.close_loading_dialog, 5)
                elif "200" <= id <= "232":
                    self.root.ids.weather_image.source = "weather/thunderstorm.png#" #store/storm.png"
                    Clock.schedule_once(self.close_loading_dialog, 5)
                elif id >= "500" and id <= "531":
                    self.root.ids.weather_image.source = "weather/havyrain.png"
                    Clock.schedule_once(self.close_loading_dialog, 5)
                    self.show_advice_dialog()
                    self.give_advice(city_name)
                elif "600" <= id <= "622":
                    self.root.ids.weather_image.source = "weather/snow.png"
                    Clock.schedule_once(self.close_loading_dialog, 5)
                    self.show_advice_dialog()
                    self.give_advice(city_name)
                elif "701" <= id <= "781":
                    self.root.ids.weather_image.source = "store/haze.png"
                    Clock.schedule_once(self.close_loading_dialog, 5)
                elif "801" <= id <= "804":
                    self.root.ids.weather_image.source = "weather/cloudy.png"
                    Clock.schedule_once(self.close_loading_dialog, 5)
                elif "300" <= id <= "321":
                    self.root.ids.weather_image.source = "weather/drizzle.png"
                    Clock.schedule_once(self.close_loading_dialog, 5)
                elif id < "200":
                    self.root.ids.weather_image.source = "weather/sunny.png"
                    Clock.schedule_once(self.close_loading_dialog, 5)
                    self.show_advice_dialog()
                    self.give_advice(city_name)
            else:
                Snackbar(text="Sorry City Not Found", snackbar_x="10dp", snackbar_y="10dp", size_hint_y=.08,
                         size_hint_x=(Window.width - (dp(10) * 2)) / Window.width, bg_color=(0, 179 / 255, 0, 1),
                         font_size="14sp").open()

        except requests.ConnectionError:
            self.show_error_dialog()
        except KeyError:
            Snackbar(text=f" '{city_name}' is not city or county name, you can't search for continent", snackbar_x="11dp",
                     snackbar_y="10dp", size_hint_y=.1,
                     size_hint_x=(Window.width - (dp(10) * 3)) / Window.width, bg_color=(0, 179 / 255, 0, 1),
                     font_size="14sp").open()

    def give_advice(self, city_name):
        API_KEY = '94cd9f95c1140a8f35c5f6267b24b046'
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&units=metric&APPID={API_KEY}"
            response = requests.get(url)
            x = response.json()
            if x["cod"] != "404":
                id = str(x["weather"][0]["id"])
                if id >= "500" and id <= "531":
                    self.show_advice_dialog()
                    self.advice_dialog.content_cls.ids.advice_image1.source = "advice_images/weather_umbrella.png"
                    self.advice_dialog.content_cls.ids.advice_image.source = "advice_images/weather_jacket.png"
                    self.advice_dialog.content_cls.ids.weather_advice.text = "Advice: Today is gonna be rainy so go with an 'umbrella' "
                elif "600" <= id <= "622":
                    self.show_advice_dialog()
                    self.advice_dialog.content_cls.ids.advice_image1.source = "advice_images/weather_jecket1.png"
                    self.advice_dialog.content_cls.ids.advice_image.source = "advice_images/weather_warmer.png"
                    self.advice_dialog.content_cls.ids.weather_advice.text = "Advice: Today is gonna be cold!. so put on a 'Jacket' "
                elif id < "200":
                    self.show_advice_dialog()
                    self.advice_dialog.content_cls.ids.advice_image1.source = "advice_images/weather_cap.png"
                    self.advice_dialog.content_cls.ids.advice_image.source = "advice_images/weather_shades.png"
                    self.advice_dialog.content_cls.ids.weather_advice.text = "Advice: Today is gonna be sunny so put on a 'Cap, Your Sun Shades and drink a lot of water' "
                else:
                    self.close_advice_dialog()

        except requests.ConnectionError:
            Snackbar(text="No Connection Please check your internet connection and check again!", snackbar_x="10dp", snackbar_y="10dp", size_hint_y=.08,
                     size_hint_x=(Window.width - (dp(10) * 2)) / Window.width, bg_color=(0, 179 / 255, 0, 1),
                     font_size="14sp").open()
        except KeyError:
            Snackbar(text=f" '{city_name}' is not city or county name, you can't search for continent", snackbar_x="11dp",
                     snackbar_y="10dp", size_hint_y=.1,
                     size_hint_x=(Window.width - (dp(10) * 3)) / Window.width, bg_color=(0, 179 / 255, 0, 1),
                     font_size="14sp").open()

    def search_weather(self):
        self.show_loading_dialog()
        city_name = self.search_weather_dialog.content_cls.ids.weather_search_input.text
        if city_name == "":
            Snackbar(text="please enter a valid city name", snackbar_x="10dp", snackbar_y="10dp",
                     size_hint_y=.08,
                     size_hint_x=(Window.width - (dp(10) * 6)) / Window.width,
                     bg_color=self.theme_cls.primary_color,
                     pos_hint={"center_x": .5, "center_y": .9},
                     font_size="14sp").open()
            self.close_loading_dialog()
        else:
            self.get_weather(city_name)
            self.get_seven_days_weather(city_name)
            self.close_weather_search_dialog()
            Clock.schedule_once(self.close_loading_dialog, 7)

    def show_error_dialog(self, *args):
        if not self.error_dialog:
            self.error_dialog = MDDialog(
                title="Error Network",
                type="custom",
                radius=[30],
                auto_dismiss=False,
                content_cls=ErrorDialogContent(),
            )

        self.error_dialog.open()

    def close_error_dialog(self):
        self.error_dialog.dismiss()


    def home_refresh(self):
        self.show_loading_dialog()
        try:
            for i in range(10):
                self.quotes_for_the_day()
            for i in range(13):
                self.most_popular_quote()
            # to add 20 different quotes of the day we use the range function
            for i in range(15):
                self.get_quotes_of_the_day()
            Clock.schedule_once(self.close_loading_dialog, 9)
        except requests.exceptions.ConnectionError:
            self.show_error_dialog()

    def refresh(self):
        self.show_loading_dialog()
        toast("loading.....")
        login_email = self.root.ids.login_email
        login_password = self.root.ids.login_password
        signup_email = self.root.ids.signup_email
        signup_password = self.root.ids.signup_password
        try:
            if self.root.ids.screen_manager.current == 'signup':
                self.send_signup_data(signup_email, signup_password)
                self.close_error_dialog()
            elif self.root.ids.screen_manager.current == 'login':
                self.retrieve_and_validate(login_email, login_password)
                self.close_error_dialog()
            elif self.root.ids.screen_manager.current == 'menu':
                self.auto_get_weather_and_location()
                self.close_error_dialog()
                for i in range(3):
                    self.get_my_quotes()
                    self.close_error_dialog()
                for i in range(30):
                    self.most_popular_quote()
                    self.close_error_dialog()
                for i in range(30):
                    self.get_quotes_of_the_day()
                    self.close_error_dialog()
                for i in range(30):
                    self.quotes_for_the_day()
                    self.close_error_dialog()
            elif self.root.ids.screen_manager.current == 'home':
                for i in range(30):
                    self.get_my_quotes()
                    self.close_error_dialog()
                for i in range(30):
                    self.most_popular_quote()
                    self.close_error_dialog()
                for i in range(30):
                    self.get_quotes_of_the_day()
                    self.close_error_dialog()
                for i in range(30):
                    self.quotes_for_the_day()
                    self.close_error_dialog()
            elif self.root.ids.screen_manager.current == 'affirmation':
                self.get_affirmed()
                self.close_error_dialog()
            elif self.root.ids.screen_manager.current == 'weather':
                city_name = self.search_weather_dialog.content_cls.ids.weather_search_input.text
                self.get_weather(city_name)
                self.close_error_dialog()
            else:
                Clock.schedule_once(self.close_loading_dialog, 14)

        except requests.ConnectionError:
            self.show_error_dialog()
        Clock.schedule_once(self.close_loading_dialog, 14)

    def get_my_quotes(self):
        my_quotes = ['"Life" is hard, but you got to show her that you are "though"',
                     "life is this, life is that, hey! that's when you let her decide, i know you are smarter than this.",
                     "you want to quit now cause it's ain't easy? it's fine but ask your self why didn't mom stop during birth?",
                     'take a nap when you are tired, but hey! "KEEP PUSHING"',
                     "Never Second Guess your Self Cause You are a god",
                     "One Day You will be heard it's a must",
                     "what ever you are doing keep doing cause most people out there doing samething are shy & scared to show it up. so keep pushing...",
                     "keep the dream big!",
                     "think twice before you act. it's important",
                     "hustle hard but not dirty",
                     "your vision is real so don't give up"
                     "value your ideas and work towards them cause you are not the only one with those same ideas."
                     ]
        author = ["Switnex xtra", "Eze .C. Goodness"]
        for i in range(1):
            self.root.ids.quotes_of_the_day_layout.add_widget(
                QuotesOfTheDaycard(qoute_of_the_day_text=random.choice(my_quotes), quote_of_the_day_author=random.choice(author),
                                   md_bg_color=rgba(randrange(180), randrange(180), randrange(180), 255)))

    def get_quotes_of_the_day(self):
        #self.text()
        try:
            url = "https://zenquotes.io/api/quotes" #"https://type.fit/api/quotes"
            response = requests.get(url)
            passed = response.json()
            quotes = passed[0]["q"]
            author = passed[1]["a"]
            toast("Done", background=self.theme_cls.accent_color)
            for i in range(1):
                self.root.ids.quotes_of_the_day_layout.add_widget(
                    QuotesOfTheDaycard(qoute_of_the_day_text=quotes, quote_of_the_day_author=author,md_bg_color=rgba(randrange(180), randrange(180), randrange(180), 255)))
        except requests.exceptions.ConnectionError:
            toast("error Network")
            self.show_error_dialog()

        except IndexError:
            toast(f"error on quotes_of_the_day try again")

    # Most Popular Quotes
    def most_popular_quote(self):
        motivation_bg_images = ["motivation_images/accessories.jpg", "motivation_images/motivation_image4.jpg",
                                "motivation_images/motivation_image5.jpg", "motivation_images/motiv3.jpg",
                                "motivation_images/motiv2.jpg",
                                "motivation_images/motivation_image3.jpg", "motivation_images/motiv2.jpg",
                                "motivation_images/motivation_image7.jpg", "motivation_images/motivation_image8.jpg",
                                "motivation_images/motivation_image9.jpg", "motivation_images/motivation_image10.jpg",
                                "motivation_images/motivation_image11.jpg",
                                "motivation_images/motivation_image13.jpg", "motivation_images/motivation_image14.jpg",
                                "motivation_images/motivation_image15.jpg", "motivation_images/motivation_image16.jpg",
                                "motivation_images/motivation_image17.jpg", "motivation_images/motivation_image18.jpg",
                                "motivation_images/motivation_image19.jpg", "motivation_images/motivation_image21.jpg",
                                "motivation_images/motivation_image22.jpg", "motivation_images/motivation_image23.jpg",
                                "motivation_images/motivation_image24.jpg", "motivation_images/motivation_image25.jpg",
                                "motivation_images/motivation_image29.jpg", ]
        url ="http://api.quotable.io/random"
        request = requests.get(url)
        responsed = request.json()
        tags = responsed["tags"]
        quotes = responsed["content"]
        author = responsed["author"]
        for i in range(1):
            self.root.ids.most_popular_quotes_layout.add_widget(MostPopularMotivation(most_popular_quotes_text=quotes,most_popular_quotes_author=author, most_popular_quote_bg_image=random.choice(motivation_bg_images)))

    # getting the Quotes for the day
    def quotes_for_the_day(self):
        motivation_bg_images = random.choice(["motivation_images/motivation_image4.jpg","motivation_images/motiv1.jpeg","motivation_images/motiv3.jpg",
                "motivation_images/accessories.jpg", "motivation_images/motivation_image4.jpg",
                 "motivation_images/motivation_image5.jpg", "motivation_images/motiv3.jpg", "motivation_images/motiv2.jpg",
                 "motivation_images/motivation_image3.jpg", "motivation_images/motiv2.jpg",
                 "motivation_images/motivation_image7.jpg", "motivation_images/motivation_image8.jpg",
                 "motivation_images/motivation_image9.jpg", "motivation_images/motivation_image10.jpg",
                 "motivation_images/motivation_image11.jpg",
                 "motivation_images/motivation_image13.jpg", "motivation_images/motivation_image14.jpg",
                 "motivation_images/motivation_image15.jpg", "motivation_images/motivation_image16.jpg",
                 "motivation_images/motivation_image17.jpg", "motivation_images/motivation_image18.jpg",
                 "motivation_images/motivation_image19.jpg", "motivation_images/motivation_image21.jpg",
                 "motivation_images/motivation_image22.jpg", "motivation_images/motivation_image23.jpg",
                 "motivation_images/motivation_image24.jpg", "motivation_images/motivation_image25.jpg",
                 "motivation_images/motivation_image29.jpg",
                "motivation_images/motiv2.jpg","motivation_images/motivation_image3.jpg","motivation_images/motiv2.jpg","motivation_images/motivation_image7.jpg", "motivation_images/motivation_image10.jpg"])
        api_url = 'https://api.api-ninjas.com/v1/quotes?'
        request = requests.get(api_url, headers={'X-Api-Key': 'PKdyDYuaaEZ2vwwPogR8WA==8LPK2F0HaIMSXkP4'})
        res = request.json()
        quotes = res[0]['quote']
        author = res[0]['author']
        for i in range(1):
            self.root.ids.quotes_for_the_day_layout.add_widget(QuotesForTheDayImageCard(quotes_for_the_day_text=quotes, quotes_for_the_day_author=author, quote_bg_image=motivation_bg_images))# quote_bg_image=motivation_bg_images[1]

    def show_home_search_dialog(self):
        if not self.home_search_dialog:
            self.home_search_dialog = MDDialog(
                title="Search For Motivations",
                type="custom",
                pos_hint={"center_y": .7},
                content_cls=HomeSearchDialogContent(),
            )

        self.home_search_dialog.open()

    def close_home_search_dialog(self, *args):
        self.home_search_dialog.dismiss()

    def search_for_quotes_for_the_day(self, *args):
        # getting search for the quotes_for_the_day
        search_input = self.home_search_dialog.content_cls.ids.motivation_search_input.text
        try:
            motivation_bg_images = ["motivation_images/accessories.jpg", "motivation_images/motivation_image4.jpg",
                 "motivation_images/motivation_image5.jpg", "motivation_images/motiv3.jpg", "motivation_images/motiv2.jpg",
                 "motivation_images/motivation_image3.jpg", "motivation_images/motiv2.jpg",
                 "motivation_images/motivation_image7.jpg", "motivation_images/motivation_image8.jpg",
                 "motivation_images/motivation_image9.jpg", "motivation_images/motivation_image10.jpg",
                 "motivation_images/motivation_image11.jpg",
                 "motivation_images/motivation_image13.jpg", "motivation_images/motivation_image14.jpg",
                 "motivation_images/motivation_image15.jpg", "motivation_images/motivation_image16.jpg",
                 "motivation_images/motivation_image17.jpg", "motivation_images/motivation_image18.jpg",
                 "motivation_images/motivation_image19.jpg", "motivation_images/motivation_image21.jpg",
                 "motivation_images/motivation_image22.jpg", "motivation_images/motivation_image23.jpg",
                 "motivation_images/motivation_image24.jpg", "motivation_images/motivation_image25.jpg",
                 "motivation_images/motivation_image29.jpg", ]
            url = f"https://api.api-ninjas.com/v1/quotes?category={search_input}"
            reqest2 = requests.get(url,
                                   headers={'X-Api-Key': 'PKdyDYuaaEZ2vwwPogR8WA==8LPK2F0HaIMSXkP4'})  # requests.get(url)
            quotes_respond = reqest2.json()
            quotes_for_the_day_quote = quotes_respond[0]['quote']
            quotes_for_the_day_author = quotes_respond[0]['author']
            self.root.ids.quotes_for_the_day_layout.add_widget(
                QuotesForTheDayImageCard(quotes_for_the_day_text=quotes_for_the_day_quote,
                                         quotes_for_the_day_author=quotes_for_the_day_author,
                                         quote_bg_image=random.choice(motivation_bg_images)))

        except IndexError:
            toast(f"no Data on {search_input} for search_for_quotes_for_the_day")
        except requests.ConnectionError:
            self.show_error_dialog()
        except requests.RequestException:
            pass

    def search_most_popular_quote(self, *args):
        search_input = self.home_search_dialog.content_cls.ids.motivation_search_input.text
        try:
            motivation_bg_images = ["motivation_images/accessories.jpg", "motivation_images/motivation_image4.jpg",
                 "motivation_images/motivation_image5.jpg", "motivation_images/motiv3.jpg", "motivation_images/motiv2.jpg",
                 "motivation_images/motivation_image3.jpg", "motivation_images/motiv2.jpg",
                 "motivation_images/motivation_image7.jpg", "motivation_images/motivation_image8.jpg",
                 "motivation_images/motivation_image9.jpg", "motivation_images/motivation_image10.jpg",
                 "motivation_images/motivation_image11.jpg",
                 "motivation_images/motivation_image13.jpg", "motivation_images/motivation_image14.jpg",
                 "motivation_images/motivation_image15.jpg", "motivation_images/motivation_image16.jpg",
                 "motivation_images/motivation_image17.jpg", "motivation_images/motivation_image18.jpg",
                 "motivation_images/motivation_image19.jpg", "motivation_images/motivation_image21.jpg",
                 "motivation_images/motivation_image22.jpg", "motivation_images/motivation_image23.jpg",
                 "motivation_images/motivation_image24.jpg", "motivation_images/motivation_image25.jpg",
                 "motivation_images/motivation_image29.jpg", ]

            # getting search for the most_popular_quote
            url = f"http://api.quotable.io/search/quotes?query={search_input}"
            request = requests.get(url)
            most_popular_response = request.json()
            most_popular_quote = most_popular_response['results'][0]['content']
            most_popular_author = most_popular_response['results'][0]['author']
            self.root.ids.most_popular_quotes_layout.clear_widgets()
            self.root.ids.most_popular_quotes_layout.add_widget(
                MostPopularMotivation(most_popular_quotes_text=most_popular_quote,
                                      most_popular_quotes_author=most_popular_author, most_popular_quote_bg_image=random.choice(motivation_bg_images)))

            most_popular_quote = most_popular_response['results'][1]['content']
            most_popular_author = most_popular_response['results'][1]['author']
            self.root.ids.most_popular_quotes_layout.add_widget(
                MostPopularMotivation(most_popular_quotes_text=most_popular_quote,
                                      most_popular_quotes_author=most_popular_author,
                                      most_popular_quote_bg_image=random.choice(motivation_bg_images)))

            most_popular_quote = most_popular_response['results'][2]['content']
            most_popular_author = most_popular_response['results'][2]['author']
            self.root.ids.most_popular_quotes_layout.add_widget(
                MostPopularMotivation(most_popular_quotes_text=most_popular_quote,
                                      most_popular_quotes_author=most_popular_author,
                                      most_popular_quote_bg_image=random.choice(motivation_bg_images)))

            most_popular_quote = most_popular_response['results'][3]['content']
            most_popular_author = most_popular_response['results'][3]['author']
            self.root.ids.most_popular_quotes_layout.add_widget(
                MostPopularMotivation(most_popular_quotes_text=most_popular_quote,
                                      most_popular_quotes_author=most_popular_author,
                                      most_popular_quote_bg_image=random.choice(motivation_bg_images)))

            most_popular_quote = most_popular_response['results'][4]['content']
            most_popular_author = most_popular_response['results'][4]['author']
            self.root.ids.most_popular_quotes_layout.add_widget(
                MostPopularMotivation(most_popular_quotes_text=most_popular_quote,
                                      most_popular_quotes_author=most_popular_author,
                                      most_popular_quote_bg_image=random.choice(motivation_bg_images)))

            most_popular_quote = most_popular_response['results'][5]['content']
            most_popular_author = most_popular_response['results'][5]['author']
            self.root.ids.most_popular_quotes_layout.add_widget(
                MostPopularMotivation(most_popular_quotes_text=most_popular_quote,
                                      most_popular_quotes_author=most_popular_author,
                                      most_popular_quote_bg_image=random.choice(motivation_bg_images)))

            most_popular_quote = most_popular_response['results'][6]['content']
            most_popular_author = most_popular_response['results'][6]['author']
            self.root.ids.most_popular_quotes_layout.add_widget(
                MostPopularMotivation(most_popular_quotes_text=most_popular_quote,
                                      most_popular_quotes_author=most_popular_author,
                                      most_popular_quote_bg_image=random.choice(motivation_bg_images)))

            most_popular_quote = most_popular_response['results'][7]['content']
            most_popular_author = most_popular_response['results'][7]['author']
            self.root.ids.most_popular_quotes_layout.add_widget(
                MostPopularMotivation(most_popular_quotes_text=most_popular_quote,
                                      most_popular_quotes_author=most_popular_author,
                                      most_popular_quote_bg_image=random.choice(motivation_bg_images)))

            most_popular_quote = most_popular_response['results'][7]['content']
            most_popular_author = most_popular_response['results'][7]['author']
            self.root.ids.most_popular_quotes_layout.add_widget(
                MostPopularMotivation(most_popular_quotes_text=most_popular_quote,
                                      most_popular_quotes_author=most_popular_author,
                                      most_popular_quote_bg_image=random.choice(motivation_bg_images)))

            most_popular_quote = most_popular_response['results'][8]['content']
            most_popular_author = most_popular_response['results'][8]['author']
            self.root.ids.most_popular_quotes_layout.add_widget(
                MostPopularMotivation(most_popular_quotes_text=most_popular_quote,
                                      most_popular_quotes_author=most_popular_author,
                                      most_popular_quote_bg_image=random.choice(motivation_bg_images)))

            most_popular_quote = most_popular_response['results'][9]['content']
            most_popular_author = most_popular_response['results'][9]['author']
            self.root.ids.most_popular_quotes_layout.add_widget(
                MostPopularMotivation(most_popular_quotes_text=most_popular_quote,
                                      most_popular_quotes_author=most_popular_author,
                                      most_popular_quote_bg_image=random.choice(motivation_bg_images)))

            most_popular_quote = most_popular_response['results'][10]['content']
            most_popular_author = most_popular_response['results'][10]['author']
            self.root.ids.most_popular_quotes_layout.add_widget(
                MostPopularMotivation(most_popular_quotes_text=most_popular_quote,
                                      most_popular_quotes_author=most_popular_author,
                                      most_popular_quote_bg_image=random.choice(motivation_bg_images)))
            most_popular_quote = most_popular_response['results'][11]['content']
            most_popular_author = most_popular_response['results'][11]['author']
            self.root.ids.most_popular_quotes_layout.add_widget(
                MostPopularMotivation(most_popular_quotes_text=most_popular_quote,
                                      most_popular_quotes_author=most_popular_author,
                                      most_popular_quote_bg_image=random.choice(motivation_bg_images)))

            most_popular_quote = most_popular_response['results'][12]['content']
            most_popular_author = most_popular_response['results'][12]['author']
            self.root.ids.most_popular_quotes_layout.add_widget(
                MostPopularMotivation(most_popular_quotes_text=most_popular_quote,
                                      most_popular_quotes_author=most_popular_author,
                                      most_popular_quote_bg_image=random.choice(motivation_bg_images)))
            most_popular_quote = most_popular_response['results'][13]['content']
            most_popular_author = most_popular_response['results'][13]['author']
            self.root.ids.most_popular_quotes_layout.add_widget(
                MostPopularMotivation(most_popular_quotes_text=most_popular_quote,
                                      most_popular_quotes_author=most_popular_author,
                                      most_popular_quote_bg_image=random.choice(motivation_bg_images)))
            most_popular_quote = most_popular_response['results'][14]['content']
            most_popular_author = most_popular_response['results'][14]['author']
            self.root.ids.most_popular_quotes_layout.add_widget(
                MostPopularMotivation(most_popular_quotes_text=most_popular_quote,
                                      most_popular_quotes_author=most_popular_author,
                                      most_popular_quote_bg_image=random.choice(motivation_bg_images)))
            most_popular_quote = most_popular_response['results'][15]['content']
            most_popular_author = most_popular_response['results'][15]['author']
            self.root.ids.most_popular_quotes_layout.add_widget(
                MostPopularMotivation(most_popular_quotes_text=most_popular_quote,
                                      most_popular_quotes_author=most_popular_author,
                                      most_popular_quote_bg_image=random.choice(motivation_bg_images)))
            most_popular_quote = most_popular_response['results'][16]['content']
            most_popular_author = most_popular_response['results'][16]['author']
            self.root.ids.most_popular_quotes_layout.add_widget(
                MostPopularMotivation(most_popular_quotes_text=most_popular_quote,
                                      most_popular_quotes_author=most_popular_author,
                                      most_popular_quote_bg_image=random.choice(motivation_bg_images)))                                                                                                        

        except IndexError:
            toast(f"no Data on {search_input} for search_for_quotes_for_the_day")
        except requests.ConnectionError:
            self.show_error_dialog()
        except requests.RequestException:
            pass

    def search_of_get_quotes_of_the_day(self):
        # getting search for get_quotes_of_the_day
        search_input = self.home_search_dialog.content_cls.ids.motivation_search_input.text
        try:
            url = f"https://free-quotes-api.herokuapp.com/{search_input}"
            req = requests.get(url)
            respond = req.json()
            if len(respond) == 0:
                toast(f"no quotes_of_the_day on '{search_input}'")
                url = f"https://free-quotes-api.herokuapp.com/"
                req = requests.get(url)
                respond = req.json()
                quotes = respond['quote']  # [x]
                author = respond['author']  # [x]
                self.root.ids.quotes_of_the_day_layout.clear_widgets()
                for i in range(5):
                    self.root.ids.quotes_of_the_day_layout.add_widget(
                        QuotesOfTheDaycard(qoute_of_the_day_text=quotes, quote_of_the_day_author=author,
                                           md_bg_color=rgba(randrange(180), randrange(180), randrange(180), 255)))
            else:
                quotes = respond['quote']  # [x]
                author = respond['author']  # [x]
                self.root.ids.quotes_of_the_day_layout.clear_widgets()
                for i in range(1):
                    self.root.ids.quotes_of_the_day_layout.add_widget(
                        QuotesOfTheDaycard(qoute_of_the_day_text=quotes, quote_of_the_day_author=author,
                                           md_bg_color=rgba(randrange(180), randrange(180), randrange(180), 255)))
        except IndexError:
            toast(f"no Data on {search_input} for search_for_quotes_for_the_day")
        except requests.ConnectionError:
            self.show_error_dialog()
        except requests.RequestException:
            pass

    def search(self):
        self.show_loading_dialog()
        for i in range(30):
            self.search_of_get_quotes_of_the_day()
        for i in range(30):
            Clock.schedule_once(self.search_for_quotes_for_the_day, 5)
        self.search_most_popular_quote()
        self.close_home_search_dialog()
        Clock.schedule_once(self.close_loading_dialog, 7)


if __name__ == "__main__":
    LabelBase.register(name="Khand",
                       fn_regular="C:\\Users\\SWITNEX XTRA\PycharmProjects\\mainapp\\font\\Khand"
                                  "-Bold.ttf")
    LabelBase.register(name="LPoppins",
                       fn_regular="C:\\Users\\SWITNEX XTRA\PycharmProjects\\mainapp\\font\\Poppins"
                                  "-Light.ttf")
    LabelBase.register(name="SPoppins",
                       fn_regular="C:\\Users\\SWITNEX XTRA\PycharmProjects\\mainapp\\font\\Poppins"
                                  "-SemiBold.ttf")
    LabelBase.register(name="Believe",
                       fn_regular="C:\\Users\\SWITNEX XTRA\PycharmProjects\\mainapp\\font\\Believeit"
                                  "-DvLE.ttf")
    XtrA().run()
