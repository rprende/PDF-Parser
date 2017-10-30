#coding=utf-8
import subprocess
import string
import csv
import argparse
from string import punctuation
import re

def pdfToText(file, page=None):
    if page is None:
        args = ['pdfToText', '-layout', '-q', file, '-']
    else:
        args = ['pdfToText', '-f', str(page), '-l', str(page), '-layout',
                '-q', file, '-']
    try:
        text = subprocess.check_output(args, universal_newlines=True)
        lines = text.splitlines()
    except subprocess.CalledProcessError:
        lines = []
    return lines

#designed for three specific PDFs
def makeGroups( file ):
	pdf = pdfToText(file)
	doc = pdf[6:len(pdf)]
	text = []
	skip = []
	entry = []
	lines = 0
	name = ''
	cutOffs = []
	phase = []
	for x in doc:
		if 'cut off' in x or 'cut-off' in x:
			cutOffs.append(x)
			continue
		elif 'Phase 1 beneficiaries' in x or 'Phase 2 beneficiaries' in x :
			phase.append(x.strip())
			continue
		elif 'February 2016 cut off' in cutOffs and 'November 2015 cut off' not in cutOffs and \
		'Phase 1 beneficiaries' in phase:
			if '\x0cHorizon 2020 SME Instrument' in x or \
			'cut off' in x or ' cut-off' in x or \
			'Proposal Acronym' in x or \
			'Phase 1 beneficiaries' in x or 'Phase 2 beneficiaries' in x or\
			'   Deadline' in x or \
			'    Call' in x:
				continue
			elif x.strip().isdigit():
				text.append("")
				continue
			elif doc.index(x) in skip:
				continue
			elif doc.index(x) == len(doc) - 1 or x == "":
				continue
			elif containsDate(x):
				entry.append(x)
				text.append(entry)
				lines = 0
				entry = []
				continue
			else:
				lines += 1
				entry.append(x)
				continue
		elif 'February 2016 cut off' not in cutOffs or \
		'November 2015 cut off' in cutOffs or \
		'Phase 2 beneficiaries' in phase:	
			if '\x0cHorizon 2020 SME Instrument' in x or \
			'cut off' in x or ' cut-off' in x or \
			'Proposal Acronym' in x or \
			'Phase 1 beneficiaries' in x or 'Phase 2 beneficiaries' in x or\
			'   Deadline' in x or \
			'    Call' in x:
				continue
			elif x.strip().isdigit():
				text.append("")
				continue
			elif doc.index(x) in skip:
				continue
			elif doc.index(x) == len(doc) - 1 or x == "":
				continue
			elif containsDate(x):
				for i in range(lines + 2):
					if i == lines + 1:
						text.append(entry)
						entry = []
						lines = 0
						continue
					else:
						entry.append(doc[doc.index(x) + i])
						skip.append(doc.index(x) + i)
			else:
				lines += 1
				entry.append(x)
				continue
	return text

def containsDate( line ):
	l = line.split()
	for word in l:
		if len(line) >= line.index(word) + 6 and (line[line.index(word):line.index(word) + 3].isdigit()) and \
		(line[line.index(word) + 4] == "-") and \
		line[line.index(word) + 5:line.index(word) + 6].isdigit():
			return True
		elif len(line) >= line.index(word) + 9 and line[line.index(word):line.index(word) + 1].isdigit() and \
		line[line.index(word) + 6 :line.index(word) + 9].isdigit() and (line[line.index(word) +5] == '/'):
			return True
		elif len(line) >= line.index(word) + 5 and line[line.index(word)].isdigit and \
		line[line.index(word) + 5 :line.index(word) + 8].isdigit() and \
		(line[line.index(word) + 4] == '/') and line[line.index(word) + 2 :line.index(word) + 3].isdigit():
			return True
		else:
			continue
	else:
		return False

def countSpaces( file ):
	doc = pdfToText(file)
	counts = []
	for l in doc:
		spaces = []
		if 'Country' in l and 'Proposal Acronym' in l:
			for word in l.split():
				if word == "City":
					spaces.append(l.index(word))
				elif word == "Beneficiary":
					spaces.append(l.index(word))
				elif word == "Website":
					spaces.append(l.index(word) + 1) #some fields were off by one to the right 
				elif word == "Proposal":
					spaces.append(l.index(word))
				elif word == "Long":
					spaces.append(l.index(word))
				elif word == "Date":
					spaces.append(l.index(word))
				elif word == "Topic":
					spaces.append(l.index(word))
				else:
					continue
		else:
			continue
		counts.append(spaces)
	return counts

def cleanURL( url ):
	url = url.lower()
	if 'http://' in url:
		url = url.replace('http://', '')
		if 'www.' in url:
			url = url.replace('www.', '')
		elif 'www2.' in url:
			url = url.replace('www2.', '')
	elif 'https://' in url:
		url = url.replace('https://', '')
		if 'www.' in url:
			url = url.replace('www.', '')
		elif 'www2.' in url:
			url = url.replace('www2.', '')
	elif 'www.' in url:
		url = url.replace('www.', '')
	elif 'www2.' in url:
		url = url.replace('www2.', '')
	elif 'ww.' in url:
		url = url.replace('ww.', '')
	return url.rstrip('/')

def makeEntries( file ):
	text = makeGroups(file)
	spaces = countSpaces(file)
	page = 0
	counts = []
	entries = [["Country", 'City', 'Beneficiary', 'Website', 'Proposal Acronym', 'Long Name', 'Call Deadline Date', 'Topic']]
	for record in text:
		if text.index(record) == (len(text) - 1) or (record == "" and spaces.index(spaces[page]) == len(spaces) - 1):
			return entries
		elif record == "": # "" is the indicator for a new page 
			page += 1
			counts = spaces[page]
			continue
		else:
			counts = spaces[page]
			e = [ '', '', '', '', '', '', '', '' ]
			for line in record:
				for word in line.split():
					if (7 <= len(line) - line.index(word)) and (line[line.index(word):line.index(word) + 3].isdigit() and \
					(line[line.index(word) + 4] == "-") and \
					line[line.index(word) + 5:line.index(word) + 6].isdigit()):
						e[6] += line[line.index(word):(line.index(word) + 7)]
						line = line.replace(line[line.index(word):line.index(word) + 7], "")
					elif (10 <= len(line) - line.index(word)) and line[line.index(word):line.index(word) + 1].isdigit() and \
					line[line.index(word) + 6 :line.index(word) + 9].isdigit() and (line[line.index(word) +5] == '/'):
					 	e[6] += line[line.index(word):line.index(word) + 10]
					 	line = line.replace(line[line.index(word):line.index(word) + 10], "")
					elif len(line) >= line.index(word) + 5 and line[line.index(word)].isdigit and \
					line[line.index(word) + 5 :line.index(word) + 8].isdigit() and \
					(line[line.index(word) + 4] == '/') and line[line.index(word) + 2 :line.index(word) + 3].isdigit():
						e[6] += line[line.index(word):line.index(word) + 9]
						line = line.replace(line[line.index(word):line.index(word) + 9], "")
				i0 = changeIndex(counts[0], line)
				e[0] += line[:i0].strip()
				if line[0] != ' ' and e[0] == '':
					e[0] += line[:line.find(' ')].strip()
				i1 = changeIndex(counts[1], line)
				e[1] += line[i0:i1].strip()
				i2 = changeIndex(counts[2], line)
				e[2] += line[i1:i2].strip()
				if '(Valencia)' in e[2]:
					e[2] = e[2].replace('(Valencia)', '')
				i3 = changeIndex(counts[3], line)
				e[3] += line[i2:i3].strip()
				i4 = changeIndex(counts[4], line)
				e[4] += line[i3:i4].strip()
				for word in e[4].split():
					if e[4] != '' and word in line and line.index(word) == i2 and word != 'wheel.me':
						e[3] = e[3] + word
						e[4] = e[4].replace(word, '')
					elif '.albacomp' in word:
						e[3] = e[3] + word
						e[4] = e[4].replace(word, '')
					else:
						continue
				i5 = changeIndex(counts[5], line)
				e[5] += line[i4:i5].strip()
				i6 = changeIndex(counts[6] - 8, line)
				e[7] += line[i6:].strip()
				e[1] = singleSpace(e[1])
				e[2] = singleSpace(e[2])
				e[5] = singleSpace(e[5])
				e[7] = singleSpace(e[7])
		e[0] = addSpace(e[0])
		e[1] = fixCity(e[2], e[1].strip())
		e[2] = preprocess_org(e[2])
		e[5] = e[5].strip()
		e[7] = e[7].strip()
		e[3] = cleanURL(e[3])
		entries.append(e)
	return entries

def changeIndex( index, line ):
	if index < len(line):
		while index > 0 and line[index - 1] != ' ':
			index -= 1
	return index

def singleSpace( s ):
	s = s.strip()
	if len(s) > 0:
		s = s + ' '
	return s

#fixes for a few formatting errors 
def addSpace( s ):
	if s == 'UnitedKingdom':
		s = 'United Kingdom'
	elif s == 'CzechRepublic':
		s = 'Czech Republic'
	return s

def fixCity( s, c ):
	if 'Vitality V' in s or 'WATERWATCH' in s:
		c = c[c.find(' ')]
	elif 'La Pobla de' in c:
		c += ' (Valencia)'
	return c

COMMON_PREFIXES = set(['the', 'koninklijk', 'koninklijke'])
COMMON_SUFFICES = set(['llc', 'zo', 'spo', 'co', 'company', 'corp','corporation','inc','ltd','limited','incorporated', 'lp', 'llp', 'gmbh',
	's l', 'o  o', 'z o o', 'kaisha', 'pte', 'ptd', 'stores', 'kft', 'ehf', 'srl', 'bv', 'sl', 'slu', 'nv', 'oy', 'sas', 'sa', 'as',
	'lda', 'doo', 'ab', 'dsp', 'pc', 'uab', 'bv', 'ag', 'cic', 'bvba', 'ivs', 'aps', 'kg', 'hf', 'spa', 'arl', 'ds', 'lcc', 'jdoo', 'sro', 's r o',
	'sha', 'shpk', 'scs', 'scpa', 'se', 'sgr', 'pty', 'nl', 'stg', 'gesbr', 'og', 'ip', 'esv', 'gie', 'vzw', 'asbl', 'vog', 'sep', 'vof', 
	'snc', 'sca', 'ebvba', 'cvba', 'cvoa', 'dd', 'ad', 'dno', 'kd', 'sp', 'bhd', 'sdn', 'adsitz', 'ead', 'eood', 'et', 'ood', 'kd', 'kda', 'sd', 
	'gp', 'plc', 'peec', 'eirl', 'ltda', 'sc', 'eu', 'senc', 'jtd', 'giu', 'zadruga', 'obrt', 'opg', 'vos', 'ks', 'ops', 'zs', 'is', 
	'ps', 'amba', 'fmba', 'smba', 'cxa', 'ep', 'sae', 'fie', 'cs', 'pe', 'eeig', 'sce', 'spe', 'ay', 'ky', 'oyj', 'osk', 'tmi', 'ry', 'rp', 
	'rs', 'ei', 'eurl', 'sasu', 'fcp', 'lic', 'oeic', 'sicav', 'icvc', 'au', 'sarl', 'scop', 'sem', 'ek', 'sll', 'mbh',
	'ekfm', 'ekfr', 'gbr', 'ohg', 'ev', 'rv', 'kgaa', 'eg', 'ae', 'ee', 'epe', 'oe', 'ovee', 'ike', 'obee', 'srlu', 
	'mepe', 'abee', 'unltd', 'ultd', 'ev', 'ec', 'bt', 'kkt', 'kht', 'kv', 'rt', 'nyrt', 'zrt', 'ohf', 'sf', 'huf', 
	'pvt', 'psu', 'ud', 'fa', 'ucits', 'bm', 'ss', 'sapa', 'scrl', 'kk', 'yk', 'gk', 'gmk', 'gsk', 'nk', 'ou', 's l',
	'tk', 'ao', 'too', 'tdo', 'kt', 'oo', 'pt', 'ptk', 'prk', 'po', 'uchr', 'sia', 'ik', 'akf', 'bo', 'sal', 'mb', 'dooel', 'kda', 
	'plt', 'sapi', 'sab', 'xk', 'xxk', 'od', 'wa', 'ba', 'ua', 'mts', 'cv', 'asa', 'ans', 'bl', 'da', 'etat', 'iks', 'kf', 'nuf', 'rhf', 
	'saog', 'saoc', 'saa', 'coop', 'ent', 'cia', 'ska', 'spj', 'spk', 'spp', 'spzoo', 'crl', 'sgps', 'pfa', 'ong', 
	'jp', 'slne', 'sad', 'scp', 'scra', 'scoop', 'hb', 'kb', 'haao', 'koop', 'dat', 'fop', 'tdv', 'tov', 'pp', 'vat', 'srls',
	'zat', 'at', 'cio', 'ccc', 'cyf', 'occ', 'na', 'ntsa', 'ncua', 'lllp', 'pllc', 'mchj', 'qmj', 'aj', 'oaj', 'yoaj', 
	'xt', 'ok', 'uk', 'qk', 'cty', 'tnhh', 'mtv', 'cp', 'dnnn', 'dntn', 'dtnn', 'htx', 'srld', u'oÜ'.encode('utf-8')]) 
PUNC_STRING = '\\' + '\\'.join([p for p in punctuation])
RE_PUNCT = re.compile('[' + PUNC_STRING + ']')
SINGLE_WHITESPACE = '\x20'

def preprocess_org(orgname):
	try:
		orgname_orig = orgname
		orgname = orgname.lower()
		orgname = remove_punctuation(orgname)
		orgname = compress_whitespace(orgname)
		orgname = remove_common_prefixes(orgname)
		orgname = remove_common_suffices(orgname)
	except (UnicodeDecodeError, IndexError) as e:
		return orgname
	return orgname

def compress_whitespace(text):
	text = re.sub('\s+', SINGLE_WHITESPACE, text).strip()
	return text

def remove_punctuation(text):
	text = re.sub(RE_PUNCT, '', text)
	return text

def remove_common_prefixes(text):
	if text.split()[0] in COMMON_PREFIXES:
		text = ' '.join(text.split()[1:])
	return text

def remove_common_suffices(text):
	for suffix in COMMON_SUFFICES:
		if suffix in text.split() and text.split().index(suffix) == len(text.split()) - 1:
			text = ' '.join(text.split()[:-1])
		elif suffix in text.split() and text.split().index(suffix) != len(text.split()) - 1:
			text = text.replace(" " + suffix + " ", '')
		else:
			continue
	return text

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='parses through a PDF and puts the data into a CSV file')
	parser.add_argument('-f', '--file', default='horizon.pdf')
	parser.add_argument( '-o', '--output', default='horizon.csv')
	args = parser.parse_args()
	with open( args.output, 'wb') as file:
		wr = csv.writer(file, quoting=csv.QUOTE_ALL)
		wr.writerows( makeEntries(args.file) )




