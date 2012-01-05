import subprocess
from xml.dom import minidom
from xml.parsers.expat import ExpatError
import simplejson

__version__ = '1.3.2'

ENV_DICT = {
    "LANG": "en_US.UTF-8",
    "PATH": "/usr/local/bin/:/usr/bin/",
    "LD_LIBRARY_PATH": "/usr/local/lib/:/usr/lib/"}


class Track(object):

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except Exception:
            pass
        return None

    def __init__(self, xml_dom_fragment):
        self.xml_dom_fragment = xml_dom_fragment
        self.track_type = self.xml_dom_fragment.attributes['type'].value
        for el in self.xml_dom_fragment.childNodes:
            if el.nodeType == 1:
                node_name = el.nodeName.lower().strip().strip('_')
                if node_name == 'id':
                    node_name = 'track_id'
                node_value = el.firstChild.nodeValue
                other_node_name = "other_%s" % node_name
                if getattr(self, node_name) is None:
                    setattr(self, node_name, node_value)
                else:
                    if getattr(self, other_node_name) is None:
                        setattr(self, other_node_name, [node_value, ])
                    else:
                        getattr(self, other_node_name).append(node_value)

        for other_property in [d for d in self.__dict__.keys() if d.startswith('other_')]:
            primary = other_property.replace('other_', '')
            try:
                setattr(self, primary, int(getattr(self, primary)))
            except Exception:
                for v in getattr(self, other_property):
                    try:
                        current = getattr(self, primary)
                        setattr(self, primary, int(v))
                        getattr(self, other_property).append(current)
                        break
                    except Exception:
                        pass

        # Handle possible Original Height and Original Width values
        height = getattr(self, "original_height")
        adjusted_height = getattr(self, "height")
        if height:
            setattr(self, "height", height)
            setattr(self, "adjusted_height", adjusted_height)

        width = getattr(self, "original_width")
        adjusted_width = getattr(self, "width")
        if width:
            setattr(self, "width", width)
            setattr(self, "adjusted_width", adjusted_width)

    def to_data(self):
        data = {}
        for k, v in self.__dict__.iteritems():
            if k != 'xml_dom_fragment':
                data[k] = v
        return data


class MediaInfo(object):

    def __init__(self, xml):
        self.xml_dom = xml
        if isinstance(xml, (str, unicode)):
            self.xml_dom = MediaInfo.parse_xml_data_into_dom(xml)

    @staticmethod
    def parse_xml_data_into_dom(xml_data):
        dom = None
        try:
            dom = minidom.parseString(xml_data)
        except ExpatError:
            try:
                dom = minidom.parseString(xml_data.replace("<>00:00:00:00</>", ""))
            except Exception:
                pass
        except Exception:
            pass
        return dom

    @staticmethod
    def parse(filename, environment=ENV_DICT):
        command = ["mediainfo", "-f", "--Output=XML", filename]
        p = subprocess.Popen(command, env=environment, stdout=subprocess.PIPE)
        stdout_data, stderr_data = p.communicate()
        xml_dom = MediaInfo.parse_xml_data_into_dom(stdout_data)
        return MediaInfo(xml_dom)

    def _populate_tracks(self):
        if self.xml_dom:
            for xml_track in self.xml_dom.getElementsByTagName("track"):
                self._tracks.append(Track(xml_track))

    @property
    def tracks(self):
        if not hasattr(self, "_tracks"):
            self._tracks = []
        if not len(self._tracks):
            self._populate_tracks()
        return self._tracks

    def to_data(self):
        data = {'tracks': []}
        for track in self.tracks:
            data['tracks'].append(track.to_data())
        return data

    def to_json(self):
        return simplejson.dumps(self.to_data())
