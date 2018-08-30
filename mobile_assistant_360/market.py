#!/usr/bin/python3

import json
import os
import shutil
import sys
import requests
from bs4 import BeautifulSoup
import bs4
from clint.textui import progress


class MobileAssistant360(object):
    """
    The class used to download android application from 360 mobile assistant store
    """

    _BASE = "http://zhushou.360.cn"
    _DETAIL = "/detail/index/soft_id/"
    _SEARCH = "/search/index/?kw="
    _CATEGORY = "/list/index/cid/"
    _CATEGORIES_ID = ["1", "2"]

    _APP_NAME = "Name"
    _APP_PACKAGE = "PackageName"
    _APP_VERSION = "Version"
    _APP_ID = "AppId"
    _APP_RATING = "Rating"
    _APP_DOWNLOADS = "Downloads"
    _APP_LINK = "DownloadLink"
    _APP_CREATOR = "Creator"
    _APP_SIZE = "Size"
    _APP_UPDATE = "LastUpdate"
    _APP_APK_NAME = "ApkName"

    _CAT_NAME = "Category"
    _CAT_ID = "CatID"

    _UNKNOWN_PACKAGE = "unknown_package"

    _TMP_FOLDER = "tmp"

    _MARKET_NAME = "MobileAssistant360"

    def __init__(self, download_folder="./"):
        self._download_folder = download_folder

    @staticmethod
    def _get_apk_package_and_version_from_url(url):
        url_split = url.split(sep="/")
        apk_name = None
        package = None
        version = None
        if url_split is not None and len(url_split) > 0 and isinstance(url_split[-1], str):
            apk = url_split[-1]
            apk_index = apk.rfind(".apk")
            if apk_index > 0:
                package = apk[:apk_index]
                apk_name = package + ".apk"
                package_split = package.split(sep="_")
                if len(package_split) >= 2 and package_split[-1].isdigit():
                    version = package_split[-1]
                    index = package.rfind("_" + version)
                    if index > 0:
                        package = package[:index]
        return apk_name, package, version

    def _get_page_apps(self, keyword, page):
        result = []
        search_url = self._BASE + self._SEARCH + keyword + "&page={}".format(page)
        req = requests.get(search_url)
        if req.status_code != 200:
            self._display_error("An error occurred with the url \"{}\".\nStatus code: {}."
                                .format(search_url, req.status_code))
            return None
        bsoup = BeautifulSoup(req.text, "html.parser")
        html_app_list = bsoup.find(attrs={'class': 'SeaCon'}).find_all("li")
        if html_app_list is None or len(html_app_list) <= 0:
            return result
        for html_app in html_app_list:
            app = {}
            title = html_app.find("h3").a["title"]
            nb_down = html_app.find(attrs={'class': 'downNum'})
            app_id = html_app.find(attrs={'class': 'download comdown'}).a['sid']
            dl_link = html_app.find(attrs={'class': 'download comdown'}).a['href']
            rate = html_app.find(attrs={'class': 'sdlft'}).contents
            if rate is not None and len(rate) == 5:
                rate = rate[2].strip()
            else:
                rate = None
            apk_name, package, version = self._get_apk_package_and_version_from_url(dl_link)
            app[self._APP_NAME] = title
            if apk_name is not None:
                app[self._APP_APK_NAME] = apk_name
            if package is not None:
                app[self._APP_PACKAGE] = package
            if version is not None:
                app[self._APP_VERSION] = version
            app[self._APP_ID] = app_id
            if rate is not None:
                app[self._APP_RATING] = rate
            app[self._APP_DOWNLOADS] = nb_down.string
            app[self._APP_LINK] = dl_link
            if type(title) is str and type(dl_link) is str:
                result.append(app)
        return result

    def search(self, keyword, nb_result=50):
        """
        Search applications according to a given keyword.

        :param keyword: A keyword used to search applications
        :type keyword: str
        :param nb_result: An integer corresponding to the limit number of application in the returned list
        :type nb_result: int
        :return: A list of applications found
        :rtype: list
        """
        if type(keyword) is not str:
            raise TypeError("Error: keyword must be a string")
        result = []
        loop = True
        page = 1
        while loop:
            apps = self._get_page_apps(keyword, page)
            page += 1
            if apps is None or len(apps) <= 0 or len(apps) + len(result) >= nb_result:
                loop = False
            if apps is not None and len(apps) > 0:
                result.extend(apps)
                if len(result) > nb_result:
                    x = len(result) - nb_result
                    result = result[:-x]
        return result

    def set_download_folder(self, download_folder):
        """
        Set a path where the application will be downloaded.

        :param download_folder: Path of the download folder
        :type download_folder: str
        """
        if not isinstance(download_folder, str):
            raise TypeError("Error: download_folder must be string")
        self._download_folder = download_folder

    @staticmethod
    def _get_title_from_details(bsoup):
        result = None
        app_name = bsoup.find(attrs={"id": "app-name"})
        if app_name is not None and app_name.span is not None and isinstance(app_name.span.get('title'), str):
            result = app_name.span['title']
        return result

    @staticmethod
    def _get_rating_from_details(bsoup):
        result = None
        s_1 = bsoup.find(attrs={"class": "s-1"})
        if s_1 is not None and len(s_1.contents) > 0 and isinstance(s_1.contents[0], str):
            result = s_1.contents[0]
        return result

    @staticmethod
    def _get_creator_from_details(bsoup):
        result = None
        base_info = bsoup.find(attrs={"class": "base-info"})
        if base_info is not None:
            tbody = base_info.find("tbody")
            if tbody is not None:
                td = tbody.findAll("td")
                if td is not None and isinstance(td, list) and len(td) > 0 and isinstance(td[0], bs4.element.Tag):
                    if isinstance(td[0].contents, list) and len(td[0].contents) > 1:
                        if isinstance(td[0].contents[1], str):
                            result = td[0].contents[1]
        return result

    @staticmethod
    def _get_update_from_details(bsoup):
        result = None
        base_info = bsoup.find(attrs={"class": "base-info"})
        if base_info is not None:
            tbody = base_info.find("tbody")
            if tbody is not None:
                td = tbody.findAll("td")
                if td is not None and isinstance(td, list) and len(td) > 1 and isinstance(td[1], bs4.element.Tag):
                    if isinstance(td[1].contents, list) and len(td[1].contents) > 1:
                        if isinstance(td[1].contents[1], str):
                            result = td[1].contents[1]
        return result

    @staticmethod
    def _get_version_from_details(bsoup):
        result = None
        base_info = bsoup.find(attrs={"class": "base-info"})
        if base_info is not None:
            tbody = base_info.find("tbody")
            if tbody is not None:
                td = tbody.findAll("td")
                if td is not None and isinstance(td, list) and len(td) > 2 and isinstance(td[2], bs4.element.Tag):
                    if isinstance(td[2].contents, list) and len(td[2].contents) > 1:
                        if isinstance(td[2].contents[1], str):
                            result = td[2].contents[1]
        return result

    @staticmethod
    def _get_size_from_details(bsoup):
        result = None
        s_3 = bsoup.findAll(attrs={"class": "s-3"})
        if s_3 is not None and len(s_3) > 1 and isinstance(s_3[1].string, str):
            result = s_3[1].string
        return result

    def _get_additional_info(self, app_id):
        result = {}
        search_url = self._BASE + self._DETAIL + str(app_id)
        req = requests.get(search_url)
        if req.status_code != 200:
            self._display_error("An error occurred with the url \"{}\".\nStatus code: {}."
                                .format(search_url, req.status_code))
            return None
        bsoup = BeautifulSoup(req.text, "html.parser")
        title = self._get_title_from_details(bsoup)
        rating = self._get_rating_from_details(bsoup)
        author = self._get_creator_from_details(bsoup)
        last_update = self._get_update_from_details(bsoup)
        version = self._get_version_from_details(bsoup)
        size = self._get_size_from_details(bsoup)
        if title is not None:
            result[self._APP_NAME] = title
        if rating is not None:
            result[self._APP_RATING] = rating
        if author is not None:
            result[self._APP_CREATOR] = author
        if last_update is not None:
            result[self._APP_UPDATE] = last_update
        if version is not None:
            result[self._APP_VERSION] = version
        if size is not None:
            result[self._APP_SIZE] = size
        return result

    @staticmethod
    def _display_warning(message):
        print("Warning: {}".format(message), file=sys.stderr)
        sys.stderr.flush()

    @staticmethod
    def _display_error(message):
        print("Error: {}".format(message), file=sys.stderr)
        sys.stderr.flush()

    def _get_download_folder(self):
        folder = self._download_folder
        if not isinstance(folder, str):
            self._display_warning("Something is wrong with download_folder. Now using the current directory.")
            folder = "./"
        return folder

    def _get_package(self, app_package):
        package = app_package
        if not isinstance(package, str):
            package = self._UNKNOWN_PACKAGE
        return package

    def _create_tmp_folder(self, download_folder):
        tmp_folder = os.path.join(download_folder, self._TMP_FOLDER)
        if os.path.exists(tmp_folder) and not os.path.isdir(tmp_folder):
            raise OSError("Error: Unable to create folder {}.".format(tmp_folder))
        elif not os.path.isdir(tmp_folder):
            os.makedirs(tmp_folder, 0o755)
        return tmp_folder

    @staticmethod
    def _create_app_folder(download_folder, package):
        app_folder = os.path.join(download_folder, package)
        if os.path.exists(app_folder) and not os.path.isdir(app_folder):
            return None
        elif not os.path.isdir(app_folder):
            os.makedirs(app_folder, 0o755)
        return app_folder

    @staticmethod
    def _get_apk_from_url(url):
        url_split = url.split(sep="/")
        apk_name = None
        if url_split is not None and len(url_split) > 0 and isinstance(url_split[-1], str):
            apk = url_split[-1]
            apk_index = apk.rfind(".apk")
            if apk_index > 0:
                apk_name = apk[:apk_index + 4]
        return apk_name

    def _create_info_file(self, app_folder, app_info):
        apk_name = app_info.get(self._APP_APK_NAME)
        if not isinstance(apk_name, str):
            self._display_error("Cannot create info file.")
            return
        info_file = self._MARKET_NAME + "_" + apk_name[:-4] + ".info"
        with open(os.path.join(app_folder, info_file), "w+") as file:
            to_write = json.dumps(app_info, ensure_ascii=False, indent=4)
            file.write(to_write)
            file.flush()

    def download(self, applications):
        """
        Download a list of application from a previous call to the search method.

        :param applications: A list of application to download from the search method call
        :type applications: list
        :return: A list of well downloaded applications
        :rtype: list
        """
        if not isinstance(applications, list):
            raise TypeError("Error: applications must be a list of applications")
        download_folder = self._get_download_folder()
        tmp_folder = self._create_tmp_folder(download_folder)
        result = []
        for application in applications:
            app_name = application.get(self._APP_NAME)
            info = None
            if isinstance(application, dict) and self._APP_ID in application and isinstance(app_name, str):
                package = self._get_package(application.get(self._APP_PACKAGE))
                app_folder = self._create_app_folder(download_folder, package)
                if app_folder is None:
                    self._display_error("Unable to create app folder for app \"{}\".\nSkip this app."
                                          .format(app_name))
                    continue
                dl_url = application.get(self._APP_LINK)
                if dl_url is None:
                    self._display_error("Unable to find a download url for app \"{}\".\nSkip this app."
                                          .format(app_name))
                    continue
                app_info = {}
                info = self._get_additional_info(application[self._APP_ID])
                if not isinstance(info, dict):
                    self._display_warning("Unable to collect information for app \"{}\".".format(app_name))
                    app_info = application
                else:
                    app_info = {**application, **info}
                version = app_info.get(self._APP_VERSION)
                apk_name = application.get(self._APP_APK_NAME)
                if not isinstance(apk_name, str):
                    apk_name = self._get_apk_from_url(dl_url)
                    if not isinstance(apk_name, str):
                        version = "" if not isinstance(version, str) else version
                        apk_name = package + version + ".apk"
                if os.path.isfile(os.path.join(app_folder, apk_name)):
                    self._display_warning("The app \"{}\" exists at \"{}\". Skip this app."
                                          .format(app_name, os.path.join(app_folder, apk_name)))
                tmp_app = os.path.join(tmp_folder, apk_name)
                try:
                    req = requests.get(dl_url, stream=True)
                    with open(tmp_app, "wb+") as apk:
                        apk_len = int(req.headers.get('content-length'))
                        chunk_size = 32 * (1 << 10)
                        for chunk in progress.bar(req.iter_content(chunk_size=chunk_size),
                                                  label="Downloading '{}': ".format(app_name),
                                                  expected_size=((apk_len/chunk_size) + 1)):
                            if chunk:
                                apk.write(chunk)
                                apk.flush()
                except IOError:
                    self._display_error("IOError exception for app \"{}\".Skip this app.".format(app_name))
                    if os.path.exists(tmp_app):
                        try:
                            os.remove(tmp_app)
                        except OSError:
                            self._display_error("Unable to remove temporary file {}.".format(tmp_app))
                    continue
                if os.path.isfile(tmp_app):
                    shutil.move(tmp_app, app_folder)
                    app_info = {**app_info, **{self._APP_APK_NAME: apk_name, self._APP_PACKAGE: package}}
                    result.append(app_info)
                    self._create_info_file(app_folder, app_info)
        try:
            os.rmdir(tmp_folder)
        except OSError:
            pass
        return result

    @staticmethod
    def _category_href_to_id(href):
        result = ""
        href_split = href.split("/")
        if len(href_split) == 1:
            result = href_split[0]
        elif len(href_split) > 1:
            href_split = href_split[-2:]
            if href_split[1]:
                result = href_split[1]
            else:
                result = href_split[0]
        return result

    def _get_categories_from_url(self, url):
        result = []
        try:
            req = requests.get(url)
            if req.status_code != 200:
                self._display_error("An error occurred with the url \"{}\".\nStatus code: {}."
                                    .format(url, req.status_code))
                return None
        except requests.exceptions.RequestException:
            self._display_error("An error occurred with the url '{}' while getting the categories.".format(url))
            return None
        try:
            bsoup = BeautifulSoup(req.text, "html.parser")
            category_list = bsoup.find(attrs={'class': 'select'}).li.findAll("a")
            if not isinstance(category_list, list) or len(category_list) <= 1:
                self._display_error("An error occurred with the url '{}' while getting the categories.".format(url))
                return None
            category_list = category_list[1:]
            for category in category_list:
                if category.string is not None and category.get('href') is not None:
                    category_name = category.string
                    category_id = self._category_href_to_id(category['href'])
                    result.append({self._CAT_NAME: category_name,
                                   self._CAT_ID: category_id})
                else:
                    self._display_warning("Something went wrong with the url '{}'.".format(url))
        except AttributeError:
            self._display_error("An error occurred with the url '{}' while getting the categories.".format(url))
            return None
        return result

    def list_categories(self):
        """
        List the existing categories.
        :return: A list of category
        """
        result = []
        for cat_id in self._CATEGORIES_ID:
            url = self._BASE + self._CATEGORY + cat_id
            ret = self._get_categories_from_url(url)
            if isinstance(ret, list) and len(ret) > 0:
                result.extend(ret)
        return result

    @staticmethod
    def _get_app_link_from_html(html):
        a_tags = html.findAll("a")
        if a_tags is not None and len(a_tags) == 3 and a_tags[2].get('href') is not None:
            href_split = a_tags[2]['href'].split("&")
            for value in reversed(href_split):
                if value[:4] == "url=" and value.rfind(".apk") != -1:
                    return value[4:]
        return None

    def _get_category_page_apps(self, category, page):
        print("a")
        result = []
        category_url = self._BASE + self._CATEGORY + category + "?page={}".format(page)
        print("b")
        try:
            req = requests.get(category_url)
            print("c")
            if req.status_code != 200:
                print("d")
                self._display_error("An error occurred with the url \"{}\".\nStatus code: {}."
                                    .format(category_url, req.status_code))
                return None
            print("e")
        except requests.exceptions.RequestException:
            print("f")
            self._display_error("An error occurred with the url '{}'.".format(category_url))
            return None
        print("g")
        try:
            bsoup = BeautifulSoup(req.text, "html.parser")
            print("h")
            html_app_list = bsoup.find(attrs={'id': 'iconList'}).find_all("li")
            print("i")
            if html_app_list is None or len(html_app_list) <= 0:
                print("j")
                return result
            for html_app in html_app_list:
                print("k")
                app = {}
                title = html_app.h3.a.string
                app_id = html_app.h3.a['sid']
                nb_down = html_app.span.string
                dl_link = self._get_app_link_from_html(html_app)
                print("l")
                if dl_link is not None:
                    print("m")
                    apk_name, package, version = self._get_apk_package_and_version_from_url(dl_link)
                    if apk_name is not None:
                        print("n")
                        app[self._APP_APK_NAME] = apk_name
                    if package is not None:
                        print("o")
                        app[self._APP_PACKAGE] = package
                    if version is not None:
                        print("p")
                        app[self._APP_VERSION] = version
                app[self._APP_NAME] = title
                app[self._APP_ID] = app_id
                app[self._APP_DOWNLOADS] = nb_down
                print("q")
                if type(title) is str and type(dl_link) is str:
                    print("r")
                    result.append(app)
        except AttributeError:
            print("s")
            self._display_error("An error occurred with the category page number {}.".format(page))
        print("t")
        return result

    def browse(self, category, nb_result=None):
        """
        Browse a category
        :param category: The ID of the category
        :param nb_result: The max number of result
        :return: A list of application
        """
        print("1")
        if type(category) is not str:
            raise TypeError("Error: category must be a string corresponding to a catID.")
        result = []
        loop = True
        page = 1
        print("2")
        while loop:
            print("3")
            apps = self._get_category_page_apps(category, page)
            print("4")
            page += 1
            print("5")
            print("apps={}".format(apps))
            if apps is None or len(apps) <= 0:
                print("6")
                loop = False
            if nb_result is not None and len(apps) + len(result) >= nb_result:
                print("6a")
                loop = False
            print("7")
            if apps is not None and len(apps) > 0:
                print("8")
                result.extend(apps)
                if len(result) > nb_result:
                    print("9")
                    x = len(result) - nb_result
                    result = result[:-x]
            print("10")
        print("11")
        return result
