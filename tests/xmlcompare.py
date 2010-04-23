from xml.etree import cElementTree as ET

def comparemany(xmls):
    xml1 = xmls[0]
    if type(xml1) == type(''):
        xml1 = ET.fromstring(xml1)
    for xml in xmls[1:]:
        xml2 = xml
        if type(xml2) == type(''):
            xml2 = ET.fromstring(xml2)
        if not compare(xml1, xml2): return False
    return True

def compare(xml1, xml2):
    if xml1.tag != xml2.tag:
        return False
    if xml1.attrib != xml2.attrib:
        return False
    for child in xml1:
        child2s = xml2.findall("%s" % child.tag)
        if child2s is None:
            return False
        found = False
        for child2 in child2s:
            found = compare(child, child2)
            if found: break
        if not found: return False
    return True
