#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import sys
import os
import unittest
import re
import sr_helpers
import datetime
import XmlHandler

from urlparse import urlparse

import Page2RSS
import argparse

#import xml.etree.ElementTree 
import lxml.etree as ET
import lxml.html as EHTML

import common
from common import is_none_or_empty

from XmlHandler import get_namespace



class SrProgramPageParser:

    def __init__(self, tracelevel):
        self.tracelevel = tracelevel
        self.url_ = None
        self.html_ = None  
        self.episodes_ = None


    @property
    def url(self):
        return self.url_

    @url.setter
    def url(self, value):
        self.url_ = value
        self.fetch_page(self.url_)

    @property
    def html(self):
        return ET.tostring(self.html_, pretty_print=True)

    @html.setter
    def html(self, value):
        try:
            self.html_ = EHTML.parse(value)
            self.trace(9, 'got page \r\n', self.html)
        except Exception, ex:
            self.trace(5, 'Failed to parse html: ', ex)
            raise


    def trace(self, level, *args):
        common.trace(level, 'SrProgramPageParser: ', args)


    def fetch_page(self, url):
        self.trace(5, 'fetching ' + url)
        self.html = EHTML.parse(url)
        self.trace(9, 'got page \r\n', ET.tostring(self.html, pretty_print=True))
        #print ET.tostring(self.html, pretty_print=True)

    def parse_page(self):

        # good links are 
        # <a href="/sida/avsnitt/587231?programid=2480&amp;playepisode=587231" aria-label="Lyssna(161 min)" class="btn btn-solid play-symbol play-symbol-wide play" data-require="modules/play-on-click">&#13;
        # <a href="/sida/avsnitt/587242?programid=2480" class="btn2 btn2-image btn2-image-foldable" data-require="modules/play-on-click">

        self.episodes_ = []

        # for timestamp_span in self.html.find('span class="page-render-timestamp hidden" data-timestamp="2015-07-28 19:11:25" />&#13;
        html_timestamp = datetime.datetime.today()
        timestamp_span = self.html.find('//span[@class="page-render-timestamp hidden"]')
        if not timestamp_span is None:
            html_timestamp = common.parse_datetime(timestamp_span.attrib['data-timestamp'])

        author_meta = self.html.find('/html/head/meta[@name="author"]')        
        self.author = author_meta.attrib['author'] if author_meta else ''

        description_meta = self.html.find('/html/head/meta[@name="description"]')        
        self.description = description_meta.attrib['description'] if description_meta else ''


        divs_to_search = self.html.findall('//div[@class="audio-box-content"]') + self.html.findall('//div[@class="audio-episode-content"]')

        def find_a_playonclick(root):
            a_play = XmlHandler.find_element_attribute(root, 'a', 'data-require', "modules/play-on-click")
            return None if a_play is None else a_play.attrib['href'] 

        """ 
            Find S�ndes-keyword and extract time from that.
        """
        def find_transmit_time(root):
            
            for span in XmlHandler.findall_element_attribute(root, 'span', 'class', 'date'):
                try:
                    abbr = span.find('abbr[@title]')
                    return sr_helpers.parse_sr_time_string(abbr.attrib['title'], html_timestamp)
                except ValueError:
                    pass
            for span in XmlHandler.findall_element_attribute(root, 'span', 'class', 'tiny-text'):
                # 2nd attempt, check text-context                
                try:
                    if span.text.find('S&#228;ndes') >= 0 or span.text.find(u'S\xe4ndes') >= 0:
                        abbr = span.find('abbr[@title]')
                        return sr_helpers.parse_sr_time_string(abbr.attrib['title'], html_timestamp)
                except ValueError:
                    pass
            return None

        def find_title(root):
            # <div class="audio-box-title">
            try:
                audio_box_title = XmlHandler.find_element_attribute(root, 'div', 'class', "audio-box-title")
                title_span = XmlHandler.find_element_attribute(audio_box_title, 'span', 'class', "responsive-audio-box-title")
                return title_span.text_content().strip()
            except AttributeError:
                pass
            # <div class="audio-episode-title audio-info">
            try:
                audio_episode_title = XmlHandler.find_element_attribute(root, 'div', 'class', "audio-episode-title audio-info")
                title_span = XmlHandler.find_element_attribute(audio_episode_title, 'span', 'class', "header2")
                return title_span.text_content().strip()
            except AttributeError:
                pass
            return None

        def find_desc(div):
            parent_div = div.getparent()
            try:
                audio_episode_body = XmlHandler.find_element_attribute(parent_div, 'div', 'class', "audio-episode-body")
                p = XmlHandler.find_element_attribute(audio_episode_body, 'p', 'class', "*preamble")
                return p.text_content().strip()
            except AttributeError:
                pass            
            try:
                audio_audiobox_body = XmlHandler.find_element_attribute(parent_div, 'div', 'class', "audio-box-body")
                p = XmlHandler.find_element_attribute(audio_audiobox_body, 'p', 'class', "preamble")
                return p.text_content().strip()
            except AttributeError:
                pass
            return None

        for div in divs_to_search:

            a_href = find_a_playonclick(div)
            if a_href is None:
                continue

            url = urlparse(a_href)
            path_parts = url.path.split('/')
            
            if len(path_parts) < 3 or path_parts[-2] != 'avsnitt':
                continue
                
            avsnitt_id = path_parts[-1]
            if avsnitt_id == '587242':
                bp= 17

            avsnitt_timestamp = find_transmit_time(div)

            avsnitt_title = find_title(div)

            avsnitt_description = find_desc(div)

            avsnitt = next((e for e in self.episodes_ if e['avsnitt'] == avsnitt_id), None)
            if avsnitt is None:
                avsnitt = {'avsnitt': avsnitt_id }
                self.episodes_.append(avsnitt)

            if not avsnitt_timestamp is None:
                avsnitt['timestamp'] = avsnitt_timestamp

            if not avsnitt_title is None:
                avsnitt['title'] = avsnitt_title

            if not avsnitt_description is None:
                avsnitt['description'] = avsnitt_description

        return self.episodes_

    def find_episodes(self):
        self.fetch_page(self.url)
        return self.parse_page()
        
    def episodes(self):
        if self.episodes_ is None:
            self.find_episodes()        
        return self.episodes_
    


def get_root(element_thing):
    # lxml.etree._ElementTree :: getroot
    if isinstance(element_thing, ET._ElementTree):
        return element_thing.getroot()
    # <type 'lxml.etree._Element'> :: getroottree
    if isinstance(element_thing, ET._Element):
        return get_root(element_thing.getroottree())
            
    return element_thing

class TestSrFetch(unittest.TestCase):
    pass


if __name__ == '__main__':
    for a in sys.argv:
        if a.find('unittest') >= 0:
            sys.exit(unittest.main())

    parser = argparse.ArgumentParser(description='My favorite argparser.')
    parser.add_argument('-l', '--tracelevel', help='Verbosity level 1 is important like error, 9 is unneeded debuginfo', default=4, type=int)
    parser.add_argument('--avsnitt', help='avsnitt', default=None, type=int, required=False)
    parser.add_argument('--progid', help='progid', default=None, type=int, required=False)
    parser.add_argument('--artikel', help='artikel', default=None, type=int, required=False)
    parser.add_argument('--url', help='use url rather than deduce from progid', default=None, required=True)

    r = parser.parse_args(None)

    common.tracelevel = r.tracelevel
    
    parser = SrProgramPageParser(common.tracelevel)
    parser.url = r.url
    episodes = parser.episodes()
    common.trace(3, 'SrProgramPageParser: result: ' , sorted(episodes, key=lambda ep: ep['avsnitt']))
    
