#!/usr/bin/env python

import io

from docutils.core import publish_parts
from flask import Flask, Markup, render_template
# from flask.ext.frozen import Freezer
from lxml import etree


app = Flask(__name__)


def format_rst(source):
    settings = dict(traceback=1, halt_level=2, initial_header_level=2)
    parts = publish_parts(
        source=source,
        writer_name="html",
        settings_overrides=settings)
    return parts


def parse_html(html):
    parser = etree.HTMLParser()
    tree = etree.parse(io.StringIO(html), parser)
    return tree


def element_as_html(element):
    html = etree.tostring(element, encoding='unicode', method='html')
    return Markup(html)


def elements_as_html(elements):
    return Markup('').join(map(element_as_html, elements))


def inner_html(element):
    chunks = []

    if element.text:
        chunks.append(element.text)

    chunks.extend(
        etree.tostring(child, encoding='unicode', method='html')
        for child in element
    )
    return Markup(''.join(chunks))


def bump_headings(element):
    d = dict(('h%d' % (n+1), 'h%d' % n) for n in range(1, 6))
    for sub in element:
        sub.tag = d.get(sub.tag, sub.tag)


def flatten_sections(element):
    # Get rid of the <div class="section" id="..."> elements. The 'id'
    # attribute is moved to the first child (the section heading).
    while True:
        section = element.find('.//div[@class="section"]')

        if section is None:
            break

        parent = section.getparent()
        pos = parent.getchildren().index(section)
        for n, child in enumerate(section.iterchildren()):
            if n == 0:
                child.set('id', section.attrib.pop('id'))
            parent.insert(pos + n, child)
        parent.remove(section)

    return element


def extract_section(parent, child):
    """Destructively extract child nodes from an element."""

    result = []
    for sibling in child.itersiblings():
        if sibling.tag == child.tag:
            break

        sibling.getparent().remove(sibling)
        result.append(sibling)

    parent.remove(child)
    result.insert(0, child)
    return result


def transform_spec(source):
    parts = format_rst(source)
    body = parse_html(parts['body']).getroot().find('body')
    doc = flatten_sections(body)
    bump_headings(doc)

    # Extract short feature descriptions
    tmp = etree.Element('tmp')
    tmp.extend(extract_section(doc, doc.find('.//*[@id="features"]')))
    tmp.remove(tmp[0])  # drop heading
    features = []
    while len(tmp):
        elements = extract_section(tmp, tmp[0])
        features.append(dict(
            title=inner_html(elements[0]),
            body=elements_as_html(elements[1:]),
        ))
    assert len(features) == 3

    # Extract all top level sections
    sections = []
    while len(doc):
        section = extract_section(doc, doc[0])
        sections.append(dict(
            id=section[0].get('id'),
            title=inner_html(section[0]),
            body=elements_as_html(section[1:]),
        ))

    # Join together all other sections for display in the template
    # text = element_as_html(doc)

    return dict(
        title=parts['title'],
        subtitle=parts['subtitle'],
        features_short=features,
        # body=text,
        sections=sections,
    )


@app.route('/')
def index():
    with open('README.rst') as fp:
        source = fp.read()
    context = transform_spec(source)
    return render_template('index.html', **context)


if __name__ == '__main__':
    # freezer = Freezer(app)
    # freezer.freeze()

    app.run(host='0', debug=True)
