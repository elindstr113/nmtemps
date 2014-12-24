#!/usr/bin/python2

from lxml import etree
OUTPUTFILE = "/home/elindstr/conkdump.txt"

colWidth = 16
url = "http://stationdata.wunderground.com/cgi-bin/stationlookup?station=KMINORTH13"
#url = "/home/elindstr/current.xml"

def main():
    nmReading = etree.parse(url)
    tempf = getValue(nmReading, "tempf")
    windspeedmph = getValue(nmReading, "windspeedmph")
    winddir = getValue(nmReading, "winddir")
    
    outputFile = open(OUTPUTFILE,"a")
    outputFile.write("Current Conditions\n")
    outputFile.write("Temperature:".ljust(colWidth) + tempf + "\n")
    outputFile.write("Wind Speed".ljust(colWidth) + windspeedmph + "\n")
    outputFile.write("Wind Direction".ljust(colWidth) + winddir + "\n")
    outputFile.close()
    
    

def getValue(xmlData, nodeName):
    return xmlData.find(".//" + nodeName).get("val")

if __name__=='__main__':
    main()

