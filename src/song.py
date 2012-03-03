#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 Deepin, Inc.
#               2011 Hou Shaohui
#
# Author:     Hou Shaohui <houshao55@gmail.com>
# Maintainer: Hou ShaoHui <houshao55@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os
import gst
import gobject
from time import time
from datetime import datetime
import traceback


import utils
from logger import Logger
import pinyin

TAG_KEYS = {"title"      : "title",
            "artist"     : "artist",
            "album"      : "album",
            "tracknumber": "#track",
            "discnumber" : "#disc",
            "genre"      : "genre",
            "date"       : "date"}

TAGS_KEYS_OVERRIDE = {}

TAGS_KEYS_OVERRIDE['Musepack'] = {"tracknumber":"track","date":"year"}

TAGS_KEYS_OVERRIDE['MP4'] = {
        "title":"\xa9nam",
        "artist":"\xa9ART",
        "album":"\xa9alb",
        "tracknumber":"trkn",
        "discnumber":"disk",
        "genre":"\xa9gen",
        "date":"\xa9day"
        }

TAGS_KEYS_OVERRIDE['ASF'] = {
        "title":"Title",
        "artist":"Author",
        "album":"WM/AlbumArtist",
        "tracknumber":"WM/TrackNumber",
        "discnumber":"WM/PartOfSet",
        "genre":"WM/Genre",
        "date":"WM/Year"
        }

USED_KEYS="""
song_type
uri title artist album genre data year 
description hidden album_colver_url station info_supp station_track_url
#track #duration #progress #disc 
#playcount #skipcount 
#lastplayed #added #date #mtime #ctime #rate #progress #bitrate #size #stream_offset
""".split()

class Song(dict, Logger):
    ''' The deepin music song class. '''
    def init_from_dict(self, other_dict=None):
        ''' init from other dict. '''
        if other_dict:
            for key in USED_KEYS:
                default = (key.startswith("#")) and 0 or None
                self[key] = other_dict.get(key, default)
        if not self.has_key("#added"):
            self["#added"] = time()
            
    def get_dict(self):        
        ''' return valid key dict. '''
        valid_dict = {}
        for key, value in self.iteritems():
            if value is not None:
                valid_dict[key] = value
        return valid_dict        
    
    def get_type(self):
        ''' return the song type. '''
        if self.has_key("song_type"):
            return self["song_type"]
        else:
            return "unknown"
        
    def set_type(self, song_type):
        ''' Set the song type. '''
        self["song_type"] = song_type
        
    def get_str(self, key, xml=False):    
        '''Get a formated version of the tag information.'''
        if key == "uri":
            value = utils.unescape_string_for_display(self.get("uri"))
        elif key == "title":    
            value = self.get("title")
            if not value:
                value = self.get_filename()
        elif key == "#bitrate":
            value = self.get("#bitrate")
            if value: value = "%dk" % value
        elif key == "#duration":    
            value = utils.duration_to_string(self.get(key))
        elif key == "#lastplayed":    
            value = self.get(key)
            if value:
                value = datetime.fromtimestamp(int(value)).strftime("%x %X")
            else:    
                value = "Never"
        elif key == "#playcount":        
            value = self.get(key) or "Never"
        elif key in ["#date", "#added"]:
            value = self.get(key)
            if value:
                value = datetime.fromtimestamp(int(value)).strftime("%x %X")
        elif key == "#rate":        
            rate = self.get("rate")
            if rate in [0,1,2,3,4,5,"0","1","2","3","4","5"]:
                value = "rate-" + str(rate)
            else: value = "rate-0"    
        elif key == "date":    
            try:
                value = self.get("date", "")[:4]
            except (ValueError, TypeError, KeyError):    
                pass
            if not value:
                value = self.get("#date")
                if value:
                    value = datetime.fromtimestamp(int(value)).strftime("%Y")
                else:    
                    value = ""
        else:            
            value = None
        if not value: value = self.get(key, "")    
        if isinstance(value, int) or isinstance(value, float): value = "%d" % value
        return value
        
    def get_filter(self):
        return " ".join([self.get_str("artist"),
                         self.get_str("album"),
                         self.get_str("title"),])
    
    def match(self, filter):
        if filter == None: return True
        search = self.get_filter()
        return len( [ s for s in filter if search.find(s) != -1 ] ) == len(filter)
        
    def get_sortable(self, key):
        '''Get sortable of the key.'''
        if key in ["album", "genre", "artist", "title"]:
            value = pinyin.transfer(self.get_str(key))
        elif key == "date":    
            value = self.get("#date")
            if not value: value = None
        else:    
            value = self.get(key)
            
        if not value and key[0] == "#": value = 0    
        return value
    
    def get_searchable(self):
        ''' Get searchable of the key, use to index'''
        title_str    = self.get_str("title")
        artist_str   = self.get_str("artist")
        title_first  = pinyin.transfer(title_str)
        artist_first = pinyin.transfer(artist_str)
        title_fill   = pinyin.transfer(title_str, False)
        artist_fill  = pinyin.transfer(artist_str, False)
        return str(title_first + artist_first +
                   title_fill + artist_fill +
                   title_str + artist_str)
    
    def __setitem__(self, key, value):
        if key == "#track":
            if value is not None and not isinstance(value,int) and value.rfind("/")!=-1 and value.strip()!="":
                value = value.strip()

                disc_nr = value[value.rfind("/"):]
                try: 
                    disc_nr = int(disc_nr)
                except: 
                    disc_nr = self.get("#disc")
                self["#disc"] = disc_nr
                value = value[:value.rfind("/")]
        elif key == "date":
            try: 
                self["#date"] = utils.strdate_to_time(value)
            except: 
                value = None
                
        if key[0] == "#":       
            try:
                if key == "#date":
                    value = float(value)
                elif key == "#duration":    
                    value = long(value)
                else:    
                    value = int(value)
            except:        
                value = None
        if value is None:        
            if key in self:
                dict.__delitem__(self, key)
        else:        
            dict.__setitem__(self, key, value)
            
    def __sort_key(self):   
        return(
                self.get_sortable("album"),
                self.get_sortable("#disc"),
                self.get_sortable("#track"),
                self.get_sortable("artist"),
                self.get_sortable("title"),
                self.get_sortable("date"),
                self.get_sortable("#bitrate"),
                self.get_sortable("uri")
                )    
    sort_key = property(__sort_key)

         
    def __call__(self, key):        
        return self.get(key)
    
    def __hash__(self):
        return hash(self.get("uri"))
    
    def __repr__(self):
        return "<Song %s>" % self.get("uri")
    
    def __cmp__(self, other_song):
        if not other: return -1
        try:
            return cmp(self.sort_key, other.sort_key)
        except AttributeError: return -1

    
    def __eq__(self, other_song):
        try:
            return self.get("uri") == other_song.get("uri")
        except:
            return False
        
    def exists(self):    
        return utils.exists(self.get("uri"))
    
    def get_path(self):
        try:
            return utils.get_path_from_uri(self.get("uri"))
        except:
            return ""
        
    def get_scheme(self):    
        return utils.get_scheme(self.get("uri"))
    
    def get_ext(self, complete=True):
        return utils.get_ext(self.get("uri"), complete)
    
    def get_filename(self):
        value = self.get("uri")
        try:
            return os.path.splitext(utils.get_name(value))[0]
        except:
            return value
        
    def read_from_file(self):    
        ''' Read song infomation for file. '''
        if self.get_scheme() == "file" and not self.exists():
            ret = False
        if self.get_scheme() == "file" and utils.file_is_supported(self.get_path()):
            ret = self.__read_from_local_file()
        else:    
            ret = self.__read_from_remote_file()
        return ret    
    
    def __read_from_local_file(self):
        try:
            path = self.get_path()
            self["#size"]  = os.path.getsize(path)
            self["#mtime"] = os.path.getmtime(path)
            self["#ctime"] = os.path.getctime(path)
            
            audio = utils.MutagenFile(self.get_path(), utils.FORMATS)
            tag_keys_override = None

            if audio is not None:
                tag_keys_override = TAGS_KEYS_OVERRIDE.get(audio.__class__.__name__, None)
                for file_tag, tag in TAG_KEYS.iteritems():
                    if tag_keys_override and tag_keys_override.has_key(file_tag):
                        file_tag = tag_keys_override[file_tag]
                    if audio.has_key(file_tag) and audio[file_tag]:    
                        value = audio[file_tag]
                        if isinstance(value, list) or isinstance(value, tuple):
                            value = value[0]
                        self[tag] = utils.fix_charset(value) # TEST

                            
                self["#duration"] = int(audio.info.length) * 1000        
                try:
                    self["#bitrate"] = int(audio.info.bitrate)
                except AttributeError: pass    
            else:    
                raise "W:Song:MutagenTag:No audio found"
        except Exception, e:    
            print "W: Error while Loading (" + self.get_path() + ")\nTracback :", e
            self.last_error = "Error while reading" + ":" + self.get_filename()
            return False
        else:
            return True
        
    def __read_from_remote_file(self):    
        ''' Load song information from remote file. '''
        
        GST_IDS = {"title"       : "title",
                   "genre"       : "genre",
                   "artist"      : "artist",
                   "album"       : "album",
                   "bitrate"     : "#bitrate",
                   'track-number':"#track"}
        is_finalize = False
        is_tagged = False
        
        def unknown_type(*param):
            raise "W:Song:GstTag:Gst decoder: type inconnu"
        
        def finalize(pipeline):
            state_ret = pipeline.set_state(gst.STATE_NULL)
            if state_ret != gst.STATE_CHANGE_SUCCESS:
                print "Failed change to null"
                
        def message(bus, message, pipeline):        
            if message.type == gst.MESSAGE_EOS:
                finalize(pipeline)
            elif message.type == gst.MESSAGE_TAG:    
                taglist = message.parse_tag()
                for key in taglist.keys():
                    if GST_IDS.has_key(key):
                        if key == "bitrate":
                            value = int(taglist[key] / 100)
                        elif isinstance(taglist[key], long):
                            value = int(taglist[key])
                        else:    
                            value = taglist[key]
                        self[GST_IDS[key]] = utils.fix_charset(value)
                        print key,":", utils.fix_charset(value)
                is_tagged = True        
                
            elif message.type == gst.MESSAGE_ERROR:    
                err, debug = message.parse_error()
                finalize(pipeline)
                raise "W:Song:GstTag:Decoder error: %s\n%s" % (err,debug)
        try:    
            try:
                url = utils.get_uri_from_path(self.get("uri").encode("utf-8"))
                print url
                pipeline = gst.parse_launch("gnomevfssrc location="+url+" ! decodebin name=decoder ! fakesink")
            except gobject.GError:    
                raise "W:Song:GstTag:Failed to build pipeline to read metadata of",self.get("uri")
            
            decoder = pipeline.get_by_name("decoder")
            decoder.connect("unknown_type", unknown_type)
            bus = pipeline.get_bus()
            bus.connect("message", message, pipeline)
            bus.add_signal_watch()
            
            state_ret = pipeline.set_state(gst.STATE_PAUSED)
            timeout = 10
            while state_ret == gst.STATE_CHANGE_ASYNC and not is_finalize and timeout > 0:
                state_ret, _state, _pending_state = pipeline.get_state(1 * gst.SECOND)
                timeout -= 1
                
            if state_ret != gst.STATE_CHANGE_SUCCESS:    
                finalize(pipeline)
                print "W:Song:GstTag:Failed Read Media"
            else:    
                if not is_tagged:
                    bus.poll(gst.MESSAGE_TAG, 5 * gst.SECOND)
                try:    
                    query = gst.query_new_duration(gst.FORMAT_TIME)
                    if pipeline.query(query):
                        total = query.parse_duration()[1]
                    else: total = 0    
                except gst.QueryError: total = 0
                total //= gst.MSECOND
                self["#duration"] = total
                if not is_tagged:
                    print "W:Song:GstTag: Media found but no tag found" 
                finalize(pipeline)    
                
        except Exception, e:        
            print "W: Error while loading ("+self.get("uri")+")\nTracback :",e
            self.last_error = ("Error while reading") + ": " + self.get_filename()
            return False
        else:
            return True
        
    def write_to_file(self):    
        ''' Save tag information to file. '''
        if self.get_scheme() != "file":
            self.last_error = self.get_scheme() + " " + "Scheme not supported"
            return False
        if not utils.exists(self.get("uri")):
            self.last_error = self.get_filename() + " doesn't exist"
            return False
        if not os.access(self.get_path(), os.W_OK):
            self.last_error = self.get_filename() + " doesn't have enough permission"
            return False
        
        try:
            audio = utils.MutagenFile(self.get_path(), utils.FORMATS)
            tag_keys_override = None
            
            if audio is not None:
                if audio.tags is None:
                    audio.add_tags()
                tag_keys_override = TAGS_KEYS_OVERRIDE.get(audio.__class__.__name__, None)    
                
                for file_tag, tag in TAG_KEYS.iteritems():
                    if tag_keys_override and tag_keys_override.has_key(file_tag):
                        file_tag = tag_keys_override[file_tag]
                        
                    if self.get(tag):    
                        value = unicode(self.get(tag))
                        audio[file_tag] = value
                    else:    
                        try:
                            del(audio[file_tag]) # TEST
                        except KeyError:
                            pass
                        
                audio.save()        
                
            else:    
                raise "w:Song:MutagenTag:No audio found"
                
        except Exception, e:    
            print traceback.format_exc()
            print "W: Error while writting ("+self.get("uri")+")\nTracback :",e
            self.last_error = "Error while writting" + ": " + self.get_filename()
            return False
        else:
            return True
        
    
if __name__ == "__main__":    
    import sys
    import utils
    song = Song()
    song.init_from_dict({"uri":sys.argv[1]})
    song.read_from_file()
    print "标题: ", song.get_str("title")
    print "艺术家: ", song.get_str("artist")
    print "专辑: ", song.get_str("album")
    print "流派: ", song.get_str("genre")
    print "歌曲总长: ", song.get_str("#duration")
    print "添加时间: ", song.get_str("#added")
    print "比特率: ", song.get_str("#bitrate")
    print "文件路径:", song.get_str("uri")
    print "排序对象: ", song.sort_key
    print "检索文本: ", song.get_searchable()
    print "查看字典: ", song.get_dict()
    # song["genre"] = "流行"
    # song["album"] = "邪恶家族"
    # song["artist"] = "小邪兽"
    # song.write_to_file()

   
    