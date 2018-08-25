import functools
import itertools
import json
import pathlib

from ._escape_utils import conditional_escape, mark_safe


class Octicon():

    def __init__(self, data):
        self.width = data['width']
        self.height = data['height']
        self.name = data['name']
        self.keywords = data['keywords']
        self.path = data['path']

    @staticmethod
    def key_exists(opts, key):
        return opts.get(key, None) is not None

    @staticmethod
    def escape_attr(key, value):
        if value is True:
            return key
        elif value is False or value is None:
            return ''
        elif key == 'class':
            if not isinstance(value, str):
                value = ' '.join(map(str.strip, value))
        return '%s="%s"' % (key, conditional_escape(value))

    def as_html(self, **opts):
        raw_attrs = self.build_attributes(opts)
        attrs = ' '.join(filter(None, itertools.starmap(
            self.escape_attr, raw_attrs.items())))
        return mark_safe("<svg %s>%s</svg>" % (attrs, self.path))

    def build_attributes(self, opts):
        key_exists = functools.partial(self.key_exists, opts)
        defaults = self.default_attrs
        opts = {k.replace('_', '-'): v for k, v in opts.items()}
        overrides = {}
        if key_exists('width') and not key_exists('height'):
            # Generate the correct height from the aspect ratio
            overrides['height'] = opts["width"] / self.size_ratio
        elif key_exists('height') and not key_exists('width'):
            # Generate the correct width from the aspect ratio
            overrides['width'] = opts["height"] * self.size_ratio
        if key_exists('class'):
            if isinstance(opts['class'], str):
                # A string.
                overrides["class"] = list(
                    *defaults['class'], *opts['class'].split())
            else:
                # An iterable of some sort.
                overrides["class"] = list(
                    *defaults['class'], *opts['class'])

        if key_exists('aria-label'):
            overrides["aria-label"] = opts["aria-label"]
            overrides["role"] = "img"
            # Un-hide the icon
            del defaults["aria-hidden"]
        out_attrs = dict(defaults)
        out_attrs.update(opts)
        out_attrs.update(overrides)
        return {
            key: value
            for key, value in out_attrs.items()
            # If we've defined custom rules on what is considered 'present'
            # Apply them here as well so that they're applied to all values
            if self.key_exists(out_attrs, key)
        }

    @property
    def size_ratio(self):
        return self.width / self.height

    @property
    def default_attrs(self):
        return {
            "version": "1.1",
            "width": self.width,
            "height": self.height,
            "viewBox": "0 0 %s %s" % (self.width, self.height),
            "class": ["octicon", "octicon-" + self.name],
            "aria-hidden": "true"
        }


class OcticonStore():

    @classmethod
    def from_file(cls, file=None):
        if file is None:
            file = pathlib.Path(__file__).parent / 'data.json'
        else:
            file = pathlib.Path(file)
        return cls(json.load(file.open()))

    def __init__(self, data_dict, *, Octicon=Octicon):
        raw_icons = [
            Octicon(data)
            for data in data_dict.values()
        ]
        self.icons = dict([
            (icon.name, icon)
            for icon in raw_icons
        ] + [
            (keyword, icon)
            for icon in raw_icons
            for keyword in icon.keywords
        ])

    def get_icon(self, name):
        return self.icons[name]

    def __getitem__(self, name):
        return self.get_icon(name)

    def get_as_html(self, name, **opts):
        return self[name].as_html(**opts)
