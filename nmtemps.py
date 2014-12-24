#!/usr/bin/python

import datetime
#import operator
#import os
import time
#from datetime import timedelta
from lxml import etree
import mysql.connector


class SVGCreator:
    topTemp = 0
    bottomTemp = 0
    left = 10
    top = 30
    grid = 10
    gridWidth = 1200
    right = gridWidth + left
    timeLineOffset = 40
    fileName = "/var/www/lindstrom/public/nmtemps.svg"
    configFileName = "/var/www/lindstrom/secure/weatherconfig.txt"

    tempData = []
    websiteList = []

    def __init__(self, fileName=""):
        if (fileName != ""):
            self.fileName = fileName
        self.loadConfigFile()
        svgString = self.createSVG()
        self.writeSVGFile(svgString)

    def writeSVGFile(self, svgString):
        if (svgString):
            try:
                svgFile = open(self.fileName, "w")
                svgFile.write(svgString)
                svgFile.close()
            except:
                print "Unable to write to file."

    def loadConfigFile(self):
        self.websiteList = [line.strip().split(",")
                            for line in open(self.configFileName, "r")
                            if line[0] != "#"]

    def createSVG(self):

        self.gridEndTime = int(datetime.datetime.now().strftime("%s"))
        self.gridStartTime = self.gridEndTime - 39600
        for site in self.websiteList:
            if site[0] == 'database':
              site += [self.getRowsFromDatabase()]
            else:
              if len(site) > 0:
                  site += [self.getWebsiteData(site[0])]
        self.setTopAndBottomTemps()
        svg = self.addXMLHeader()
        svg += self.addGraphBorder()
        svg += self.drawHorizontalLinesInGrid()
        svg += self.drawVerticalLinesInGrid()
        for site in self.websiteList:
            url, color, name, siteData = site
            svg += self.addTemperatureGraph(siteData, color.strip())
        svg += self.addTimeAndTemperatureLabels()
        svg += self.addLegend()
        svg += "</svg>\n"
        return svg


    def getRowsFromDatabase(self):
        dbConn = mysql.connector.connect(host="localhost",
                                         user="phpuser",
                                         passwd="dbaccess",
                                         db="Raspi")
        dbCursor = dbConn.cursor()
        selectCommand = ("SELECT date, temperature "
                         "from temperatures "
                         "where date > DATE_SUB(NOW(), INTERVAL 11 HOUR) "
                         "ORDER BY date DESC LIMIT 200")
        dbCursor.execute(selectCommand)
        dbRows = dbCursor.fetchall()
        dbCursor.close()
        dbConn.close()
        siteData = []
        for row in dbRows:
          observation = row[0]
          temperature = row[1]
          siteData.append([observation.strftime('%H:%M:%S'),"{0:.2f}".format(temperature),int(observation.strftime("%s"))])
        return siteData


    def getWebsiteData(self, weatherURL):
        nmTempData = etree.parse(weatherURL)
        siteData = []
        for observation in nmTempData.xpath('//current_observation'):
            temp_f = observation.find("temp_f").text
            observationTimeStamp = observation.find(
                "observation_time_rfc822").text
            timeCorrection = datetime.timedelta(hours=-4)
            observationTime = datetime.datetime.strptime(
                observationTimeStamp,
                "%a, %d %b %Y %H:%M:%S %Z") + timeCorrection
            observationTimeInSeconds = int(
                observationTime.strftime("%s"))
            if (self.gridStartTime <=
                observationTimeInSeconds <=
                self.gridEndTime and
                float(temp_f) > 0):
                siteData.append([observationTime.strftime('%H:%M:%S'),
                                 temp_f, observationTimeInSeconds])
        return siteData

    def setTopAndBottomTemps(self):
        allTemperatures = []
        for site in self.websiteList:
            for tempData in site[3]:
                allTemperatures += [tempData[1]]
        tempsSorted = sorted(allTemperatures, key=float)
        self.bottomTemp = int((5 * round(float(tempsSorted[0]) / 5))) - 10
        self.topTemp = int((5 * round(float(tempsSorted[-1]) / 5))) + 10
        self.height = (self.topTemp - self.bottomTemp) * self.grid
        self.bottom = self.height + self.top

    def addXMLHeader(self):
        header = "<?xml version='1.0' standalone='no'?>"
        header += ("<svg xmlns='http://www.w3.org/2000/svg' height='800px' width='1350px'>")
        return header

    def addGraphBorder(self):
        return ("<path d='M %d,%d %d,%d %d,%d %d,%d %d,%d' style='fill:none; stroke:#000000;stroke-width:1px;stroke-linecap:butt; stroke-linejoin:miter;stroke-opacity:1' />" %
                (self.left, self.top, self.right, self.top,
                 self.right, self.bottom, self.left, self.bottom,
                 self.left, self.top))

    def drawHorizontalLinesInGrid(self):
        grdLines = ""
        for yIndex in range(self.top + self.grid, self.bottom, self.grid):
            color = "FF0000" if (yIndex + self.top - self.grid) % 50 == 0 \
                else "dddddd"
            grdLines += ("<line x1='%d' y1='%d' x2='%d' y2='%d' style='stroke:#%s;'/>" %
                         (self.left, yIndex, self.right, yIndex, color))
        return grdLines

    def drawVerticalLinesInGrid(self):
        gridLines = ""
        color = "dddddd"
        for xIndex in range(self.left, self.right, self.grid):
            gridLines += ('<line x1="%d" y1="%d" x2="%d" y2="%d" style="stroke:#%s;"/>' %
                          (xIndex, self.top, xIndex, self.bottom, color))
        return gridLines

    def addTemperatureGraph(self, siteData, lineColor):
        graphPoints = self.createListOfTemperaturePoints(siteData)
        return ("<path d='M " + graphPoints + "' style='fill:none;stroke:#" + lineColor + ";stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />")

    def createListOfTemperaturePoints(self, siteData):
        path = ""
        for tempLine in siteData:
            temp = tempLine[1]
            currentTimeStamp = int(tempLine[2])
            x = (((currentTimeStamp - self.gridStartTime) /
                 float(self.gridEndTime - self.gridStartTime)) *
                 self.gridWidth + 10)
            path += (str(x) + "," +
                     str(
                         self.bottom - (float(temp) -
                          (self.topTemp - (self.height / 10))) * 10) +
                     " ")
        return path.rstrip()

    def addTimeAndTemperatureLabels(self):
        labels = ""
        startTime = self.gridStartTime
        endTime = self.gridEndTime

        for currentTime in range(startTime, endTime + 1, 1800):
            x = ((currentTime - startTime) / float(endTime - startTime)
                 ) * self.gridWidth + 10
            ts = time.strftime("%H:%M", time.localtime(currentTime))

            labels += "<text x='%d' y='%d' style='stroke:none;fill:#000000; font-size:12px;text-align:right;' transform='rotate(270 %d,%d)'>%s</text>" % \
                    (x + 5, self.bottom + self.timeLineOffset, x + 5,
                     self.bottom + self.timeLineOffset, ts)

        labels += "<text xml:space='preserve' style='font-size:12px; font-style:normal;font-weight:normal;text-align:start; line-height:125%;letter-spacing:0px;word-spacing:0px;text-anchor:start;fill:#ff0000;fill-opacity:1;stroke:none;font-family:Sans'>"

        for temp in range(self.topTemp, self.bottomTemp, -5):
            labels += "<tspan x='%s' y='%s'>%s&#176;</tspan>" % \
            (str(self.right + 5),
             str(self.top + ((self.topTemp - temp) * self.grid) + 3),
             temp)

        labels += "</text>"

        return labels

    def addLegend(self):
        labels = "<text xml:space='preserve' style='font-size:12px;font-style:normal;font-weight:normal;text-align:start;line-height:125%;letter-spacing:0px;word-spacing:0px;text-anchor:start;fill:#000000;fill-opacity:1;stroke:none;font-family:Sans'>"
        x = 10
        for site in self.websiteList:
            url, color, name, data = site
            labels += "<tspan x='%d' y='%d' style='fill:#%s'>%s</tspan>" % \
                        (x, 20, color.strip(), name.strip())
            x += 150
        labels += "</text>"
        return labels


if __name__ == '__main__':
    Creator = SVGCreator()
