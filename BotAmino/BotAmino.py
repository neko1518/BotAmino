from time import sleep as slp
from sys import exit
import requests
import json
from json import dumps, load
from pathlib import Path
from threading import Thread
# from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from urllib.request import urlopen
from datetime import datetime
from random import choice

from .local_amino import Client, SubClient, ACM
from .commands import *
from .extensions import *

from uuid import uuid4

# this is Slimakoi's API with some of my patches

# API made by ThePhoenix78
# Big optimisation thanks to SempreLEGIT#1378 ♥
# small very small changes by meliodas
# if login method is not working use sid

path_utilities = "utilities"
path_amino = f'{path_utilities}/amino_list'
path_client = "client.txt"
NoneType = type(None)


with suppress(Exception):
    for i in (path_utilities, path_amino):
        Path(i).mkdir(exist_ok=True)


def print_exception(exc):
    print(repr(exc))


class BotAmino(Command, Client, TimeOut, BannedWords):
    def __init__(self, email: str = None, password: str = None, sid: str = None,  proxies: dict = None, deviceId: str = "2271017D5F917B37DAC9C325B10542BC9B63109292D882729D1813D5355404380E2F1A699A34629C10", certificatePath: str = None):
        Command.__init__(self)
        Client.__init__(self, proxies=proxies, deviceId=deviceId, certificatePath=certificatePath)

        if email and password:
            self.login(email=email, password=password)
        elif sid:
            self.login_sid(SID=sid)
        else:
            try:
                with open(path_client, "r") as file_:
                    para = file_.readlines()
                self.login(email=para[0].strip(), password=para[1].strip())
            except FileNotFoundError:
                with open(path_client, 'w') as file_:
                    file_.write('email\npassword')
                print("Please enter your email and password in the file client.txt")
                print("-----end-----")
                exit(1)

        self.communaute = {}
        self.botId = self.userId
        self.len_community = 0
        self.perms_list = []
        self.prefix = "!"
        self.activity = False
        self.wait = 0
        self.bio = None
        self.self_callable = False
        self.no_command_message = ""
        self.spam_message = "You are spamming, be careful"
        self.lock_message = "Command locked sorry"
        self.launched = False

    def tradlist(self, sub):
        sublist = []
        for elem in sub:
            with suppress(Exception):
                val = self.get_from_code(f"http://aminoapps.com/u/{elem}").objectId
                sublist.append(val)
                continue
            sublist.append(elem)
        return sublist

    def send_data(self, data):
        self.send(data)

    def add_community(self, comId):
        self.communaute[comId] = Bot(self, comId, self.prefix, self.bio, self.activity)

    def get_community(self, comId):
        return self.communaute[comId]

    def is_it_bot(self, uid):
        return uid == self.botId and not self.self_callable

    def is_it_admin(self, uid):
        return uid in self.perms_list

    def get_wallet_amount(self):
        return self.get_wallet_info().totalCoins

    def generate_transaction_id(self):
        return str(uuid4())

    def start_screen_room(self, comId: str, chatId: str, joinType: int=1):
        data = {
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "joinRole": joinType,
                "id": "2154531"  # Need to change?
            },
            "t": 112
        }
        data = dumps(data)
        self.send(data)

        data = {
            "o": {
                "ndcId": int(comId),
                "threadId": chatId,
                "joinRole": joinType,
                "channelType": 5,
                "id": "2154531"  # Need to change?
            },
            "t": 108
        }
        data = dumps(data)
        self.send(data)

    def join_screen_room(self, comId: str, chatId: str, joinType: int=1):
        data = {
            "o":
                {
                    "ndcId": int(comId),
                    "threadId": chatId,
                    "joinRole": 2,
                    "id": "72446"
                },
            "t": 112
        }
        data = dumps(data)
        self.send(data)

    def start_voice_room(self, comId: str, chatId: str, joinType: int=1):
        data = {
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "joinRole": joinType,
                "id": "2154531"  # Need to change?
            },
            "t": 112
        }
        data = dumps(data)
        self.send(data)
        data = {
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "channelType": 1,
                "id": "2154531"  # Need to change?
            },
            "t": 108
        }
        data = dumps(data)
        self.send(data)

    def end_voice_room(self, comId: str, chatId: str, joinType: int = 2):
        data = {
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "joinRole": joinType,
                "id": "2154531"  # Need to change?
            },
            "t": 112
        }
        data = dumps(data)
        self.send(data)

    def show_online(self, comId):
        data = {
            "o": {
                "actions": ["Browsing"],
                "target": f"ndc://x{comId}/",
                "ndcId": int(comId),
                "id": "82333"
            },
            "t":304}
        data = dumps(data)
        slp(2)
        self.send(data)

    def upload_bubble(self,file,comId):
        data=file
        response = requests.post(f"https://service.narvii.com/api/v1/x{comId}/s/chat/chat-bubble/templates/107147e9-05c5-405f-8553-af65d2823457/generate", data=data, headers=self.headers)
        bid=json.loads(response.text)['chatBubble']['bubbleId']
        print(bid)
        response = requests.post(f"https://service.narvii.com/api/v1/x{comId}/s/chat/chat-bubble/{bid}", data=data, headers=self.headers)
        if response.status_code !=200:
            return json.loads(response.text)
        else: return bid

    def check(self, args, *can, id_=None):
        id_ = id_ if id_ else args.authorId
        foo = {'staff': args.subClient.is_in_staff,
               'bot': self.is_it_bot}

        for i in can:
            if foo[i](id_):
                return True

    def check_all(self):
        amino_list = self.sub_clients()
        for com in amino_list.comId:
            try:
                self.communaute[com].check_in()
            except Exception:
                pass

    def threadLaunch(self, commu, passive: bool=False):
        self.communaute[commu] = Bot(self, commu, self.prefix, self.bio, passive)
        slp(30)
        if passive:
            self.communaute[commu].passive()

    def launch(self, passive: bool = False):
        amino_list = self.sub_clients()
        self.len_community = len(amino_list.comId)
        [Thread(target=self.threadLaunch, args=[commu, passive]).start() for commu in amino_list.comId]

        if self.launched:
            return

        if self.categorie_exist("command") or self.categorie_exist("answer"):
            self.launch_text_message()

        if self.categorie_exist("on_member_join_chat"):
            self.launch_on_member_join_chat()

        if self.categorie_exist("on_member_leave_chat"):
            self.launch_on_member_leave_chat()

        if self.categorie_exist("on_other"):
            self.launch_other_message()

        if self.categorie_exist("on_remove"):
            self.launch_removed_message()

        if self.categorie_exist("on_delete"):
            self.launch_delete_message()

        if self.categorie_exist("on_all"):
            self.launch_all_message()

        if self.categorie_exist("on_event"):
            self.launch_on_event()

        self.launched = True

    def single_launch(self, commu, passive: bool = False):
        amino_list = self.sub_clients()
        self.len_community = len(amino_list.comId)
        Thread(target=self.threadLaunch, args=[commu, passive]).start()

        if self.launched:
            return

        if self.categorie_exist("command") or self.categorie_exist("answer"):
            self.launch_text_message()

        if self.categorie_exist("on_member_join_chat"):
            self.launch_on_member_join_chat()

        if self.categorie_exist("on_member_leave_chat"):
            self.launch_on_member_leave_chat()

        if self.categorie_exist("on_other"):
            self.launch_other_message()

        if self.categorie_exist("on_remove"):
            self.launch_removed_message()

        if self.categorie_exist("on_delete"):
            self.launch_delete_message()

        if self.categorie_exist("on_all"):
            self.launch_all_message()

        self.launched = True

    def message_analyse(self, data, type):
        try:
            commuId = data.comId
            subClient = self.get_community(commuId)
        except Exception:
            return

        args = Parameters(data, subClient)
        Thread(target=self.execute, args=[type, args, type]).start()

    def on_member_event(self, data, type):
        try:
            commuId = data.comId
            subClient = self.get_community(commuId)
        except Exception:
            return

        args = Parameters(data, subClient)

        if not self.check(args, "bot"):
            Thread(target=self.execute, args=[type, args, type]).start()

    def launch_text_message(self):
        @self.event("on_text_message")
        def on_text_message(data):
            try:
                commuId = data.comId
                subClient = self.get_community(commuId)
            except Exception:
                return

            args = Parameters(data, subClient)

            if "on_message" in self.commands.keys():
                Thread(target=self.execute, args=["on_message", args, "on_message"]).start()

            if not self.check(args, 'staff', 'bot') and subClient.banned_words:
                self.check_banned_words(args)

            if not self.timed_out(args.authorId) and args.message.startswith(subClient.prefix) and not self.check(args, "bot"):
                subClient.send_message(args.chatId, self.spam_message)
                return

            elif "command" in self.commands.keys() and args.message.startswith(subClient.prefix) and not self.check(args, "bot"):
                print(f"{args.author} : {args.message}")
                command = args.message.lower().split()[0][len(subClient.prefix):]

                if command in subClient.locked_command:
                    subClient.send_message(args.chatId, self.lock_message)
                    return

                args.message = ' '.join(args.message.split()[1:])
                self.time_user(args.authorId, self.wait)
                if command.lower() in self.commands["command"].keys():
                    Thread(target=self.execute, args=[command, args]).start()

                elif self.no_command_message:
                    subClient.send_message(args.chatId, self.no_command_message)
                return

            elif "answer" in self.commands.keys() and args.message.lower() in self.commands["answer"] and not self.check(args, "bot"):
                print(f"{args.author} : {args.message}")
                self.time_user(args.authorId, self.wait)
                Thread(target=self.execute, args=[args.message.lower(), args, "answer"]).start()
                return

    def launch_other_message(self):
        for type_name in ("on_strike_message", "on_voice_chat_not_answered",
                          "on_voice_chat_not_cancelled", "on_voice_chat_not_declined",
                          "on_video_chat_not_answered", "on_video_chat_not_cancelled",
                          "on_video_chat_not_declined", "on_voice_chat_start", "on_video_chat_start",
                          "on_voice_chat_end", "on_video_chat_end", "on_screen_room_start",
                          "on_screen_room_end", "on_avatar_chat_start", "on_avatar_chat_end"):

            @self.event(type_name)
            def on_other_message(data):
                self.message_analyse(data, "on_other")

    def launch_all_message(self):
        for x in (self.chat_methods):
            @self.event(self.chat_methods[x].__name__)
            def on_all_message(data):
                self.message_analyse(data, "on_all")

    def launch_delete_message(self):
        @self.event("on_delete_message")
        def on_delete_message(data):
            self.message_analyse(data, "on_delete")

    def launch_removed_message(self):
        for type_name in ("on_chat_removed_message", "on_text_message_force_removed", "on_text_message_removed_by_admin", "on_delete_message"):
            @self.event(type_name)
            def on_chat_removed(data):
                self.message_analyse(data, "on_remove")

    def launch_on_member_join_chat(self):
        @self.event("on_group_member_join")
        def on_group_member_join(data):
            self.on_member_event(data, "on_member_join_chat")

    def launch_on_member_leave_chat(self):
        @self.event("on_group_member_leave")
        def on_group_member_leave(data):
            self.on_member_event(data, "on_member_leave_chat")

    def launch_on_event(self):
        for k, v in self.commands["on_event"].items():
            @self.event(k)
            def _function(data):
                v(data)


class Bot(SubClient, ACM):
    def __init__(self, client, community, prefix: str = "!", bio=None, activity=False) -> None:
        self.client = client
        self.marche = True
        self.prefix = prefix
        self.bio_contents = bio
        self.activity = activity

        if isinstance(community, int):
            self.community_id = community
            self.community = self.client.get_community_info(comId=self.community_id)
            self.community_amino_id = self.community.aminoId
        else:
            self.community_amino_id = community
            self.informations = self.client.get_from_code(f"http://aminoapps.com/c/{community}")
            self.community_id = self.informations.json["extensions"]["community"]["ndcId"]
            self.community = self.client.get_community_info(comId=self.community_id)

        self.community_name = self.community.name

        super().__init__(comId=self.community_id, profile=self.client.profile)

        try:
            self.community_leader_agent_id = self.community.json["agent"]["uid"]
        except Exception:
            self.community_leader_agent_id = "-"

        try:
            self.community_staff_list = self.community.json["communityHeadList"]
        except Exception:
            self.community_staff_list = ""

        if self.community_staff_list:
            self.community_leaders = [elem["uid"] for elem in self.community_staff_list if elem["role"] in (100, 102)]
            self.community_curators = [elem["uid"] for elem in self.community_staff_list if elem["role"] == 101]
            self.community_staff = [elem["uid"] for elem in self.community_staff_list]

        if not Path(f'{path_amino}/{self.community_amino_id}.json').exists():
            self.create_community_file()

        old_dict = self.get_file_dict()
        new_dict = self.create_dict()

        def do(k, v): old_dict[k] = v
        def undo(k): del old_dict[k]

        [do(k, v) for k, v in new_dict.items() if k not in old_dict]
        [undo(k) for k in new_dict.keys() if k not in old_dict]

        self.update_file(old_dict)

        # self.subclient = SubClient(comId=self.community_id, profile=client.profile)

        self.banned_words = self.get_file_info("banned_words")
        self.locked_command = self.get_file_info("locked_command")
        self.message_bvn = self.get_file_info("welcome")
        self.welcome_chat = self.get_file_info("welcome_chat")
        self.prefix = self.get_file_info("prefix")
        self.favorite_users = self.get_file_info("favorite_users")
        self.favorite_chats = self.get_file_info("favorite_chats")
        self.update_file()
        #self.activity_status("on")
        new_users = self.get_all_users(start=0, size=30, type="recent")

        self.new_users = [elem["uid"] for elem in new_users.json["userProfileList"]]

    def create_community_file(self):
        with open(f'{path_amino}/{self.community_amino_id}.json', 'w', encoding='utf8') as file:
            dict = self.create_dict()
            file.write(dumps(dict, sort_keys=False, indent=4))

    def create_dict(self):
        return {"welcome": "", "prefix": self.prefix, "welcome_chat": "", "locked_command": [], "favorite_users": [], "favorite_chats": [], "banned_words": []}

    def get_dict(self):
        return {"welcome": self.message_bvn, "prefix": self.prefix, "welcome_chat": self.welcome_chat, "locked_command": self.locked_command,
                "favorite_users": self.favorite_users, "favorite_chats": self.favorite_chats, "banned_words": self.banned_words}

    def update_file(self, dict=None):
        if not dict:
            dict = self.get_dict()
        with open(f"{path_amino}/{self.community_amino_id}.json", "w", encoding="utf8") as file:
            file.write(dumps(dict, sort_keys=False, indent=4))

    def get_file_info(self, info: str = None):
        with open(f"{path_amino}/{self.community_amino_id}.json", "r", encoding="utf8") as file:
            return load(file)[info]

    def get_file_dict(self, info: str = None):
        with open(f"{path_amino}/{self.community_amino_id}.json", "r", encoding="utf8") as file:
            return load(file)

    def get_banned_words(self):
        return self.banned_words

    def set_prefix(self, prefix: str):
        self.prefix = prefix
        self.update_file()

    def set_welcome_message(self, message: str):
        self.message_bvn = message.replace('"', '“')
        self.update_file()

    def set_welcome_chat(self, chatId: str):
        self.welcome_chat = chatId
        self.update_file()

    def add_favorite_users(self, value: str):
        self.favorite_users.append(value)
        self.update_file()

    def add_favorite_chats(self, value: str):
        self.favorite_chats.append(value)
        self.update_file()

    def add_banned_words(self, liste: list):
        self.banned_words.extend(liste)
        self.update_file()

    def add_locked_command(self, liste: list):
        self.locked_command.extend(liste)
        self.update_file()

    def remove_favorite_users(self, value: str):
        liste = [value]
        [self.favorite_users.remove(elem) for elem in liste if elem in self.favorite_users]
        self.update_file()

    def remove_favorite_chats(self, value: str):
        liste = [value]
        [self.favorite_chats.remove(elem) for elem in liste if elem in self.favorite_chats]
        self.update_file()

    def remove_banned_words(self, liste: list):
        [self.banned_words.remove(elem) for elem in liste if elem in self.banned_words]
        self.update_file()

    def remove_locked_command(self, liste: list):
        [self.locked_command.remove(elem) for elem in liste if elem in self.locked_command]
        self.update_file()

    def unset_welcome_chat(self):
        self.welcome_chat = ""
        self.update_file()

    def is_in_staff(self, uid):
        return uid in self.community_staff

    def is_leader(self, uid):
        return uid in self.community_leaders

    def is_curator(self, uid):
        return uid in self.community_curators

    def is_agent(self, uid):
        return uid == self.community_leader_agent_id

    def accept_role(self, rid: str = None):
        with suppress(Exception):
            self.accept_organizer(rid)
            return True
        with suppress(Exception):
            self.promotion(noticeId=rid)
            return True
        return False

    def get_staff(self, community):
        if isinstance(community, int):
            with suppress(Exception):
                community = self.client.get_community_info(com_id=community)
        else:
            try:
                informations = self.client.get_from_code(f"http://aminoapps.com/c/{community}")
            except Exception:
                return False

            community_id = informations.json["extensions"]["community"]["ndcId"]
            community = self.client.get_community_info(comId=community_id)

        try:
            community_staff_list = community.json["communityHeadList"]
            community_staff = [elem["uid"] for elem in community_staff_list]
        except Exception:
            community_staff_list = ""
        else:
            return community_staff

    def get_user_id(self, name_or_id):
        members = self.get_all_users(size=1).json['userProfileCount']
        start = 0
        lower_name = None

        while start <= members:
            users = self.get_all_users(start=start, size=100).json['userProfileList']
            for user in users:
                name = user['nickname']
                uid = user['uid']

                if name_or_id == name or name_or_id == uid:
                    return (name, uid)
                if not lower_name and name_or_id.lower() in name.lower():
                    lower_name = (name, uid)
            start += 100

        return lower_name if lower_name else None

    def ask_all_members(self, message, lvl: int = 20, type_bool: int = 1):
        def ask(uid):
            try:
                self.start_chat(userId=[uid], message=message)
            except Exception:
                self.start_chat(userId=[uid], message=message)

        size = self.get_all_users(start=0, size=1, type="recent").json['userProfileCount']
        st = 0

        while size > 0:
            value = size
            if value > 100:
                value = 100
            users = self.get_all_users(start=st, size=value)
            if type_bool == 1:
                [ask(user["uid"]) for user in users.json['userProfileList'] if user['level'] == lvl]
            elif type_bool == 2:
                [ask(user["uid"]) for user in users.json['userProfileList'] if user['level'] <= lvl]
            elif type_bool == 3:
                [ask(user["uid"]) for user in users.json['userProfileList'] if user['level'] >= lvl]
            size -= 100
            st += 100

    def ask_amino_staff(self, message):
        self.start_chat(userId=self.community_staff, message=message)

    def get_chat_id(self, chat: str = None):
        with suppress(Exception):
            return self.get_from_code(f"http://aminoapps.com/c/{chat}").objectId

        val = self.get_public_chat_threads()
        for title, chat_id in zip(val.title, val.chatId):
            if chat == title:
                return chat_id

        for title, chat_id in zip(val.title, val.chatId):
            if chat.lower() in title.lower() or chat == chat_id:
                return chat_id
        return False

    def copy_bubble(self, chatId:str, replyId:str, comId:str):
        header={
            'Accept-Language': 'en-US',
            'Content-Type': 'application/octet-stream',
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 7.1; LG-UK495 Build/MRA58K; com.narvii.amino.master/3.3.33180)',
            'Host': 'service.narvii.com',
            'Accept-Encoding': 'gzip',
            'Connection': 'Keep-Alive',
        }
        a=self.get_message_info(chatId=chatId,messageId=replyId).json["chatBubble"]["resourceUrl"]
        with urlopen(a) as zipresp:
            yo=zipresp.read()

        response = requests.post(f"https://service.narvii.com/api/v1/x{comId}/s/chat/chat-bubble/templates/107147e9-05c5-405f-8553-af65d2823457/generate", data=yo, headers=header)
        bid=json.loads(response.text)['chatBubble']['bubbleId']
        response = requests.post(f"https://service.narvii.com/api/v1/{comId}/s/chat/chat-bubble/{bid}", data=yo, headers=header)


    def stop_instance(self):
        self.marche = False

    def start_instance(self):
        self.marche = True
        Thread(target=self.passive).start()

    def leave_amino(self):
        self.marche = False
        for elem in self.get_public_chat_threads().chatId:
            with suppress(Exception):
                self.leave_chat(elem)
        self.client.leave_community(comId=self.community_id)

    def check_new_member(self):
        if not (self.message_bvn or self.welcome_chat):
            return
        new_list = self.get_all_users(start=0, size=25, type="recent")
        new_member = [(elem["nickname"], elem["uid"]) for elem in new_list.json["userProfileList"]]
        for elem in new_member:
            name, uid = elem[0], elem[1]

            val = self.get_wall_comments(userId=uid, sorting='newest').commentId

            if not val and self.message_bvn:
                with suppress(Exception):
                    self.comment(message=self.message_bvn, userId=uid)

            if not val and self.welcome_chat:
                with suppress(Exception):
                    self.invite_to_chat(chatId=self.welcome_chat, userId=uid)

        new_users = self.get_all_users(start=0, size=30, type="recent")
        self.new_users = [elem["uid"] for elem in new_users.json["userProfileList"]]

    def welcome_new_member(self):
        new_list = self.get_all_users(start=0, size=25, type="recent")
        new_member = [(elem["nickname"], elem["uid"]) for elem in new_list.json["userProfileList"]]
        for elem in new_member:
            name, uid = elem[0], elem[1]
            val = self.get_wall_comments(userId=uid, sorting='newest').commentId

            if not val or uid not in self.new_users and self.message_bvn:
                with suppress(Exception):
                    self.comment(message=self.message_bvn, userId=uid)

            if uid not in self.new_users and self.welcome_chat:
                with suppress(Exception):
                    self.invite_to_chat(chatId=self.welcome_chat, userId=uid)

        new_users = self.get_all_users(start=0, size=30, type="recent")
        self.new_users = [elem["uid"] for elem in new_users.json["userProfileList"]]

    def feature_chats(self):
        for elem in self.favorite_chats:
            with suppress(Exception):
                self.favorite(time=2, chatId=elem)

    def feature_users(self):
        featured = [elem["uid"] for elem in self.get_featured_users().json["userProfileList"]]
        for elem in self.favorite_users:
            if elem not in featured:
                with suppress(Exception):
                    self.favorite(time=1, userId=elem)

    def get_member_level(self, uid):
        return self.get_user_info(userId=uid).level

    def get_member_titles(self, uid):
        with suppress(Exception):
            return self.get_user_info(userId=uid).customTitles
        return False

    def get_wallet_amount(self):
        return self.client.get_wallet_info().totalCoins

    def generate_transaction_id(self):
        return str(uuid4())

    def pay(self, coins: int = 0, blogId: str = None, chatId: str = None, objectId: str = None, transactionId: str = None):
        if not transactionId:
            transactionId = self.generate_transaction_id()
        self.send_coins(coins=coins, blogId=blogId, chatId=chatId, objectId=objectId, transactionId=transactionId)

    def favorite(self, time: int = 1, userId: str = None, chatId: str = None, blogId: str = None, wikiId: str = None):
        self.feature(time=time, userId=userId, chatId=chatId, blogId=blogId, wikiId=wikiId)

    def unfavorite(self, userId: str = None, chatId: str = None, blogId: str = None, wikiId: str = None):
        self.unfeature(userId=userId, chatId=chatId, blogId=blogId, wikiId=wikiId)

    def join_chatroom(self, chat: str = None, chatId: str = None):
        if not chat:
            with suppress(Exception):
                self.join_chat(chatId)
                return ""

        with suppress(Exception):
            chati = self.get_from_code(f"{chat}").objectId
            self.join_chat(chati)
            return chat

        chats = self.get_public_chat_threads()
        for title, chat_id in zip(chats.title, chats.chatId):
            if chat == title:
                self.join_chat(chat_id)
                return title

        chats = self.get_public_chat_threads()
        for title, chat_id in zip(chats.title, chats.chatId):
            if chat.lower() in title.lower() or chat == chat_id:
                self.join_chat(chat_id)
                return title

        return False

    def start_screen_room(self, chatId: str, joinType: int=1):
        self.client.join_video_chat(comId=self.community_id, chatId=chatId, joinType=joinType)

    def start_voice_room(self, chatId: str, joinType: int=1):
        self.client.join_voice_chat(comId=self.community_id, chatId=chatId, joinType=joinType)

    def join_screen_room(self, chatId: str, joinType: int=1):
        self.client.join_video_chat_as_viewer(comId=self.community_id, chatId=chatId, joinType=joinType)

    def get_chats(self):
        return self.get_public_chat_threads()

    def join_all_chat(self):
        for elem in self.get_public_chat_threads().chatId:
            with suppress(Exception):
                self.join_chat(elem)

    def leave_all_chats(self):
        for elem in self.get_public_chat_threads().chatId:
            with suppress(Exception):
                self.leave_chat(elem)

    def follow_user(self, uid):
        self.follow(userId=[uid])

    def unfollow_user(self, uid):
        self.unfollow(userId=uid)

    def add_title(self, uid: str, title: str, color: str = None):
        member = self.get_member_titles(uid)
        try:
            titles = [i['title'] for i in member] + [title]
            colors = [i['color'] for i in member] + [color]
        except TypeError:
            titles = [title]
            colors = [color]

        self.edit_titles(uid, titles, colors)
        return True

    def remove_title(self, uid: str, title: str):
        member = self.get_member_titles(uid)
        tlist = []
        clist = []

        for t in member:
            if t["title"] != title:
                tlist.append(t["title"])
                clist.append(t["color"])
        self.edit_titles(uid, tlist, clist)
        return True

    def passive(self):
        def upt_activity():
            timeNow = int(datetime.timestamp(datetime.now()))
            timeEnd = timeNow + 300
            try:
                self.send_active_obj(startTime=timeNow, endTime=timeEnd)
            except Exception:
                pass

        def change_bio_and_welcome_members():
            if self.welcome_chat or self.message_bvn:
                Thread(target=self.welcome_new_member).start()
            try:
                if isinstance(self.bio_contents, list):
                    self.edit_profile(content=choice(self.bio_contents))

                elif isinstance(self.bio_contents, str):
                    self.edit_profile(content=self.bio_contents)
            except Exception as e:
                print_exception(e)

        def feature_chats():
            try:
                Thread(target=self.feature_chats).start()
            except Exception as e:
                print_exception(e)

        def feature_users():
            try:
                Thread(target=self.feature_users).start()
            except Exception as e:
                print_exception(e)

        feature_chats()
        feature_users()

        j = 0
        k = 0
        while self.marche:
            change_bio_and_welcome_members()
            if j >= 24:
                feature_chats()
                j = 0
            if k >= 288:
                feature_users()
                k = 0

            if self.activity:
                try:
                    self.activity_status('on')
                except Exception:
                    pass
                upt_activity()

            slp(300)
            j += 1
            k += 1
