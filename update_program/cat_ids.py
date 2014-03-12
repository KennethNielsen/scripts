import xml.etree.ElementTree as XML

# NOTE: UPDATE SCRIPT TO TAKE ID/FILENAME FROM id FILE
ID_FILE = None

doc = XML.parse(ID_FILE)

for channel in doc.findall('.//channel'):
    # The id attribute looks like this: www.ontv.dk/tv/10066
    idstring = channel.attrib['id'].split('/')[2]
    name = channel[0].text
    print '{: <8}: {}'.format(idstring, name)
