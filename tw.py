import twitter, re, time, codecs, random, cPickle, os, glob

################################################################################
# Script to make a large twitter corpus that has regional information on the   #
# basis of the reported location of the twitter user. This approach is less    #
# fast than tapping in on the Twitter hose and filtering on the geocoding of   #
# the tweet. This approach, however, is more conservative because it ignores   #
# the mobility of the twitter user.                                            #
# Tom Ruette, 14 september 2012                                                #
#                                                                              #
# tw.py: main script to which you should provide:                              #
# - twitter credentials                                                        #
# - list of initial seeds                                                      #
# - list of locations (in a files cities.txt, one location per line)           #
#                                                                              #
# Remarks:                                                                     #
# - twitter module is python-twitter (not easy_install version, but the url:   #
#   https://code.google.com/p/python-twitter/                                  #
################################################################################

# how many twitter users do you want?
convergence = 100000

# provide your Twitter credentials (get them at the twitter website)
api = twitter.Api(consumer_key='',
consumer_secret='', 
access_token_key='', 
access_token_secret='')

# provide here a number of seeds (people from the region you want to scrape
# with lots of friends, e.g. newspapers or politicians. Make sure they
# report their location. These will be used to set things in motion.
new_seeds = [""]
			
################################################################################

def addLocation(slist):
	""" ad hoc method to grab the reported location of usernames in a list """
	out = []
	fin = codecs.open("cities.txt", "r", "utf-8")
	locations = fin.readlines()
	fin.close()
	for s in slist:
		s = s.split("\t")[0]
		l = api.GetUser(s).location
		for loc in locations:
			loc = loc.strip()
			if loc.lower() in l.lower():
				l = loc.lower()
				print s, l
				out.append( unicode(s + "," + l))
				break
	return out

def acceptableLocation(l):
	""" ad hoc method to check if a reported location l is in a list of wanted
	locations cities.txt """
	out = False
	fin = codecs.open("cities.txt", "r", "utf-8")
	locations = fin.readlines()
	fin.close()
	for loc in locations:
		if loc.strip().lower() in l.lower():
			out = loc.strip()
			break
	return out

def newseeds(seedlist):
	""" ad hoc method that grabs the friends in acceptable locations from the
	seeds in seedlist """
	out = []
	i = 1
	random.shuffle(seedlist)
	for sl in seedlist:
		print i, "of", len(seedlist)
		i+=1
		s = sl.split(",")[0]
		try:
			time.sleep(11.5)
			friends = api.GetFriends(user=s)
			for friend in friends:
				floc = unicode(friend.location)
				floc = acceptableLocation(floc)
				if floc != False:
					print "doing:", unicode(friend.screen_name + "," + floc)
					out.append(unicode(friend.screen_name + "," + floc))
		except Exception,e:
			print e
	return out
	
def doInitCheck():
	""" the initcheck consists of checking if some usernames were found yet """
	try:
		fin = open("unames.txt", "r")
		fin.close()
		return False
	except:
		return True
	
def unique(l):
	""" silly method to remove duplicates from a list """
	out = []
	for i in l:
		if i not in out:
			out.append(i)
	return out

################################################################################

# verify if this script was run already
initcheck = doInitCheck()

# if this is the first run, initialize the working space
if initcheck == True:
	os.system("mkdir locations") # make the necessary directory for the corpus
	seeds = addLocation(new_seeds) # add the location to these seeds
	# and save this information
	fout = open("unames.txt", "w")
	fout.write("\n".join(seeds))
	fout.close()

# grab the usernames that were already present
fin = open("unames.txt", "r")
seeds = fin.readlines()
fin.close()

# keep finding new seeds until convergence
while len(seeds) < convergence:
	print "there are now", len(seeds), "seeds"
	new_seeds = newseeds(seeds)
	seeds.extend(new_seeds)
	seeds = unique(seeds)
	fin = codecs.open("unames.txt", "w", encoding="utf-8")
	fin.write("\n".join(seeds))
	fin.close()

print "got all the seeds we need! Moving on to retrieving the seed's tweets."

# to be on the safe side, we read in the lates unames.txt
fin = open("unames.txt", "r")
unames = fin.readlines()
fin.close()

# remove the twitter users that were already scraped
done = []
donefs = glob.glob("./locations/*/*.tweets")
for donef in donefs:
        username = ".".join(donef.split("/")[-1].split(".")[:-1])
        done.append(username)
unamesfilter = []
for uname in unames:
	name = uname.split(",")[0]
	if name not in done:
   		unamesfilter.append(uname)

# how many users are we speaking about? Print some information
print "input", len(unames)
print "done", len(done)
print "todo", len(unamesfilter)

# go through the remaining users and download their tweets, which are stored in
# folder that bears the name of the location.
random.shuffle(unamesfilter)
for uname in unamesfilter:
	name = uname.split(",")[0] # username
	loc = ",".join(uname.split(",")[1:]).strip() # normalized location
	print name, "in", loc
	print "\tsearching for statuses"
	time.sleep(10) # sleep as there is a limited amount of calls to twitter
	try:
		# the following call gets all the data
		tl = api.GetUserTimeline(name, include_entities=False, count=200)
		print "\tfound", len(tl), "statuses"
		# store will carry the xml that we are going to output
		store = "<tweets>\n"
		# go through the data that was retrieved from twitter
		for s in tl:
			date = s.created_at # data
			identifier = str(s.id) # tweet id
			text = s.text # tweet itself
			# the xml
			out = unicode("<tweet date=\"" + date + "\" id=\"" + identifier + 
					"\">" + text + "</tweet>\n")
			store = store + out
		store = store.strip() + "\n</tweets>" # close the xml
		# if this is the first observation in this location, init the folder
		if str("./locations/" + loc) not in glob.glob("./locations/*"):
			print "making the directory"
			os.system("mkdir ./locations/" + loc)
		# save the xml
		fout = codecs.open("./locations/" + loc + "/" + name + ".tweets", "w", 
							encoding="utf-8")
		fout.write(unicode(store))
		fout.close()
	# if something goes wrong, just ignore it, continue and it will be tried 
	# again later
	except Exception, e:
		print "\terror", e
		continue