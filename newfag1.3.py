import urllib, sys, time, pickle

## The following code changes the User-Agent so search results won't prompt a
## 403 error. See http://wolfprojects.altervista.org/changeua.php
class AppURLopener(urllib.FancyURLopener):
    version = "sup/1.0"

urllib._urlopener = AppURLopener()

###############################################################################

class NewFagMeter:
    ''' 
    Purpose: 
         To compile data on /a/nons favourite shows, and to link this to how
         many shows they've watched
    
    Class fields: 
    
         seriesList 
            - A list of anime series
         
         seriesWeights 
            - The list of corresponding weights
        
         hiddenWeight
            - a constant used for linear classification.

         binaryThreshold
            - The show count that divides newfags from oldfags, for binary
            classification. This will be determined later, but is set now
            at 100
         
         namesDBFile
            - A pickled namesDB file
            
         namesDB
            - A dictionary that has a record of previously processed names
         
         M 
            - A matrix of the training data. M[i][j] will return the i'th
            user's j'th favourite series. M[i][0] is the i'th users show count
              
    Initialization:
         The first arg is a txtfile with the format
         
               # of shows seen for user 1
               show 1
               show 2
               ...
               show 9
               -
               # of shows seen for user 1
               show 1
               show 2
               ...
                         
         To standardize series names, the input is put into a google search,
         then the first wikipedia link found is parsed to find the name.
         
         The second arg is the name of a pickle file, which will be converted
         to the instances nameConversion field
               
    Methods:
    
         naiveLearn
            - A naive learning algorithm. The weight of the series is simply
            the average of show counts for the set of users where that series
            is present.
            
         linearClassifyScore
            - It takes in a list of 9 shows. For every hit in the database,
            it averages the weights of those scores and returns that value.
            
         binaryClassifyScore
            - It takes in a list of 9 shows, and averages all the weights. If a
            show is not found in the list, that data point is simply ignored in
            the calculation, and a message is printed indicating the miss.
            
         binaryISE
            - It takes a binary classifier and outputs the in-sample error.
            
         getMedianScore
            - returns the median of the number of shows people have watched
            
         getMeanScore
            - returns the mean of the number of shows people have watched
    
    Functions:
        
         parseData
            - It takes in a txtfile (raw data), a conversions database file, and
            a conversions dictionary and outputs a list of the data.
            
         parseTitle
            - takes in an unprocessed series name and standardizes it with
            the goole/wikipedia method
        
        loadDB
            - Takes in the name of a pickled dictionary and returns the dict
            
    TODO:
    
         Long Term
            - Modify classify method to work on 3x3's. It should use google 
              reverse image search to obtain the series name
              
            - Automate the collection of training data
            
            - Create a stronger learning algorithm
            
            - Implement a database in mysql to save training data
            
            - Improve the standardization algorithm to first use a table lookup
              to improve time efficiency
            
         Short Term
            - Create a survey monkey form to collect data better
         
            - Improve readability of docstring
         
            - Create a wiki
         
            - Gain feedback on improvements to be made
         
    '''
    def __init__(self, txtFile, dbFile):
        
        self.seriesList = []
        self.seriesWeights = []
        self.hiddenWeight = 0
        self.binaryThreshold = 50
        self.seriesDBFile = dbFile
        self.seriesDB = loadDB(dbFile)
        self.M = parseData(txtFile, dbFile, loadDB(dbFile))
        self.popularityList = []       
        
        for user in self.M:
            for show in user[1:]:
                if show not in self.seriesList:
                    self.seriesList.append(show)
                    
        for show in self.seriesList:
            popularity = 0
            for user in self.M:
                if show in user[:]:
                    popularity += 1
            self.popularityList.append(popularity)
            
    def parseTitle(self, show):
        return parseTitle(show, self.seriesDBFile, self.seriesDB)
    
    def addNameMapping(self, show, name):
        self.seriesDB[show] = name
        output = open(self.seriesDBFile, 'wb')
        pickle.dump(self.seriesDB, output)
        output.close()
 
    def findMappings(self, name):
        result = []
        if name in self.seriesDB.values():
            for show in self.seriesDB.keys():
                if self.seriesDB[show] == name:
                    result += show
        return result
        
    
    def naiveLearn(self):
        for show in self.seriesList:
            totalWeight = 0
            viewCount = 0.0
            for user in self.M:
                if show in user[1:]:
                    totalWeight += user[0]
                    viewCount += 1
            self.seriesWeights.append(totalWeight / viewCount)
    
    def getWeight(self, show, standardize = True):
        if standardize:
            show = parseTitle(show, self.seriesDBFile, self.seriesDB)
        if show in self.seriesList:
            return self.seriesWeights[self.seriesList.index(show)]
        else:
            return "Show not in database"
    
    def linearClassifyScore(self, inputlist, standardize = True):
        score = 0
        total = 0
        for show in inputlist:
            if standardize:
                show = parseTitle(show, self.seriesDBFile, self.seriesDB)
            if show in self.seriesList:
                score += self.seriesWeights[self.seriesList.index(show)]
                total += 1.0
        return score / total
    
    def binaryClassifyScore(self, inputlist, standardize = True):
        if self.linearClassifyScore(inputlist, standardize) >= self.binaryThreshold:
            return 1
        else:
            return -1
    
    def binaryISE(self):
        error = 0.0
        total = 0.0
        for user in self.M:
            if user[0] >= self.binaryThreshold:
                actual = 1
            else:
                actual = -1
                
            if actual != self.binaryClassifyScore(user[1:], False):
                error += 1
            total += 1
        return error * 100 / total    
    
    def getMedianScore(self):
        userScores = []
        for user in self.M:
            userScores.append(user[0])
        userScores.sort()
        
        if len(userScores) % 2 == 0:
            return userScores[len(userScores)/ 2]
        else:
            return userScores[(len(userScores) + 1)/ 2]
            
    def getMeanScore(self):
        totalUserScore = 0.0
        numberOfUsers = 0.0
        for user in self.M:
            totalUserScore += user[0]
            numberOfUsers += 1
        return totalUserScore / numberOfUsers
    
    def getPopularity(self, show, standardize = True):
        if standardize:
            show = parseTitle(show, self.seriesDBFile, self.seriesDB)
        if show in self.seriesList:
            return self.popularityList[self.seriesList.index(show)]
        else:
            return "Show not in database"
    
    def linearClassifyPop(self, inputlist, standardize = True):
        pop = 0
        total = 0
        for show in inputlist:
            if standardize:
                show = parseTitle(show, self.namesDBFile, self.namesDB)
            if show in self.seriesList:
                pop += self.popularityList[self.seriesList.index(show)]
                total += 1.0
        return pop / total    
    
    def ithPopular(self, i):
        pL = self.popularityList[:]
        sL = self.seriesList[:]
        lst = [x for (y,x) in sorted(zip(pL, sL))]
        result = lst[-i]
        pL.sort()
        return result, pL[-i]

    def ithHipster(self, i):
        i -= 1
        pL = self.popularityList[:]
        sL = self.seriesList[:]
        lst = [x for (y,x) in sorted(zip(pL, sL))]
        result = lst[i]
        pL.sort()
        return result, pL[i]
    
    def printPopularityScale(self):
        pL = self.popularityList[:]
        sL = self.seriesList[:]
        lst = [x for (y,x) in sorted(zip(pL, sL))]
        pL.sort()
        lst.reverse()
        for i, show in enumerate(lst):
            print "Rank:" + str(i + 1), "| Title: " + show, 
            print "- " +str(pL[-i - 1]) 
    
    def ithLargest(self, i):
        sW = self.seriesWeights[:]
        sL = self.seriesList[:]
        lst = [x for (y,x) in sorted(zip(sW, sL))]
        result = lst[-i]
        sW.sort()
        return result, sW[-i]
    
    def ithSmallest(self, i):
        i -= 1
        sW = self.seriesWeights[:]
        sL = self.seriesList[:]
        lst = [x for (y,x) in sorted(zip(sW, sL))]
        result = lst[i]
        sW.sort()
        return result, sW[i]
    
    def printPowerLevelScale(self):
        sW = self.seriesWeights[:]
        sL = self.seriesList[:]
        lst = [x for (y,x) in sorted(zip(sW, sL))]
        sW.sort()
        lst.reverse()
        for i, show in enumerate(lst):
            print "Rank:" + str(i + 1), "| Title: " + show, 
            print "- " + str(sW[-i - 1])  
    
    def userBaseSize(self):
        return len(self.M)
    
    def numberShows(self):
        return len(self.seriesList)

            
        

def parseData(txtfile, dbFile, database):
    
    result = []
    data = open(txtfile, 'r')
    i = -1
    for line in data:
        i += 1
        if i % 10 == 0:
            try:
                dataPoint = [int(line[:-1])] # the number of shows
            except:
                sys.stderr.write("input file not valid at line " + str(i))
                sys.exit(1)
        elif i % 10 == 9:
            if dataPoint in result:
                sys.stderr.write("duplicate detected at line " + str(i))
                sys.exit(1)               
            result.append(dataPoint)
        else:
            title = parseTitle(line[:-1], dbFile, database)
            #print "input: " + line[:-1]
            #print "output: " + title
            dataPoint.append(title)
    data.close()
    
    return result        

def parseTitle(title, dbFile, database):
    title = title.lower()
    
    if title in database.keys():
        #print "already found :"
        return database[title]
    
    #print "querying google"
    time.sleep(5)
    templateURL = "http://www.google.com/search?q="

    url = urllib.urlopen(templateURL + title + "+anime+site:wikipedia.org")
    source = url.read()
    start = source.find("http://en.wikipedia.org/wiki/") + 29
    end = start
    while source[end] != "&" and source[end] != "%":
        end += 1
    if end - start > 100:
        seriesName = "Unknown"
        #print "Error, series unknown"
        #print title
        sys.exit(1)
    else:
        seriesName = source[start:end]
        
        #update database and dbFile
        database[title] = seriesName
        output = open(dbFile, 'wb')
        pickle.dump(database, output)
        output.close()
        
    return seriesName

def loadDB(dbFile):
    print "loading database"
    pkl_file = open(dbFile, 'rb')
    database = pickle.load(pkl_file)
    pkl_file.close()
    return database

Detector = NewFagMeter("data.txt", "anime.pkl")
Detector.naiveLearn()
print "classification error: ", str(Detector.binaryISE())+ "%"
print "mean :", Detector.getMeanScore()
print "median :", Detector.getMedianScore()
print "most oldfag show:", Detector.ithLargest(1)
print "most newfag show:", Detector.ithSmallest(1)
print "most popular show:", Detector.ithPopular(1)
print "most hipster show:", Detector.ithHipster(1)
print "number of entries:", Detector.userBaseSize()
print "number of shows:", Detector.numberShows()
print "popularity scale: "
Detector.printPopularityScale()
print "power level scale: "
Detector.printPowerLevelScale()
a = raw_input()
