import argparse
import os
import paramiko
import sys
from scp import SCPClient, SCPException
import time

import config

from profanityfilter import ProfanityFilter
pf = ProfanityFilter()

SETUP_MODE = 0
BUILD_WORD_ALIGN_CORPUS = 1
GET_GOOD_SENTENCES = 3

debug = False



# SETUP


# Copies the python utility file on the server and creates the sentence aligned file from the OPUS corpus
def setup(lang, output_file=config.output_file):
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	conn = ssh.connect(hostname=config.host, username=config.user, password=config.password, port=config.port)

	#Copy python file on server:
	try:
		scp = SCPClient(ssh.get_transport())
		scp.put(config.local_folder + config.server_utils, remote_path=config.remote_folder)
	except SCPException as error:
		print(error)
		ssh.close()
		return

	#Execute files on server
	if debug:
		print('Calling:','cd '+ config.remote_folder +'; python3.7 '+ config.server_utils + ' -M ' + str(SETUP_MODE) + ' -o ' + output_file + ' -l ' + lang)
	stdin, stdout, stderr = ssh.exec_command('(cd '+ config.remote_folder +'; python3.7 '+ config.server_utils + ' -M ' + str(SETUP_MODE) + ' -o ' + output_file + ' -l ' + lang +' -n 1)', timeout=10*60)
	print(stderr.readlines(), file=sys.stderr)
	print(stdout.readlines())

	#Retrieves output
	try:
		scp.get(config.remote_folder + output_file)
	except SCPException as error:
		print(error)

	ssh.close()



# BUILD_WORD_ALIGN_CORPUS


# Obtains the priors file trained for each language if present
def __get_eflomal_priors(lang):
	if lang == 'iten':
		return config.eflomal_priors_iten
	elif lang == 'sven':
		return config.eflomal_priors_sven
	elif lang == 'svit':
		return config.eflomal_priors_svit
	return None


# Checks if the sentence contains profanity
def __is_clean(sent):
	return pf.is_clean(sent)


# Calls eflomal to obtain the word alignment and copy it on the server
def call_eflomal(lang, output_file=config.output_file, eflomal_f_alignment_file=config.eflomal_f_alignment_file, eflomal_r_alignment_file=config.eflomal_r_alignment_file):
	clean_file = "cleaned_" + output_file
	ids_file = "ids_" + output_file

	#Removes files from a previous run
	if os.path.exists(eflomal_f_alignment_file):
		os.remove(eflomal_f_alignment_file)
	if os.path.exists(eflomal_r_alignment_file):
		os.remove(eflomal_r_alignment_file)

	with open(output_file) as f:
		with open(clean_file, "a") as cl_f:
			with open(ids_file, "a") as id_f:
				for line in f.readlines():
					tokens = line.split("|||")
					if not tokens or len(tokens) != 3:
						pass
					elif not tokens[0].strip() or not tokens[1].strip() or not tokens[2].strip():
						pass
					elif not __is_clean(tokens[1]) or not __is_clean(tokens[2]):
						pass
					else:
						id_f.write(tokens[0] + "\n")
						cl_f.write(tokens[1] + "|||" + tokens[2])

	command = config.eflomal_path + '/align.py -i ' + clean_file 
	eflomal_priors = __get_eflomal_priors(lang)
	if eflomal_priors and os.path.exists(eflomal_priors):
		command += ' -p ' + eflomal_priors
	command_for = command + ' -f ' + eflomal_f_alignment_file
	command_rev = command + ' -r ' + eflomal_r_alignment_file
	res = os.system(command_for)
	res = os.system(command_rev)

	os.remove(output_file)
	with open(output_file, "a") as out:
		with open(clean_file) as cl_f:
			with open(ids_file) as id_f:
				clean_sent = cl_f.readlines()
				ids = id_f.readlines()
				for i in range(len(clean_sent)):
					out.write(ids[i].strip()+"|||"+clean_sent[i])
	
	os.remove(clean_file)
	os.remove(ids_file)

	#Copy eflomal file on server:
	if res == 0:
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		conn = ssh.connect(hostname=config.host, username=config.user, password=config.password, port=config.port)
		try:
			scp = SCPClient(ssh.get_transport())
			scp.put(eflomal_f_alignment_file, remote_path=config.remote_folder)
			scp.put(eflomal_r_alignment_file, remote_path=config.remote_folder)
			scp.put(output_file, remote_path=config.remote_folder)
		except SCPException as error:
			print(error)
		ssh.close()

		print(eflomal_f_alignment_file,' : ',eflomal_r_alignment_file)
	else:
		print("An error occured while calling eflomal.")



# GET_GOOD_SENTENCES


# Selects good sentences using the files from SETUP and BUILD_WORD_ALIGN_CORPUS
def get_good_sentences(lang, output_file=config.output_file, eflomal_f_alignment_file=config.eflomal_f_alignment_file, eflomal_r_alignment_file=config.eflomal_r_alignment_file):
	chosen_sent = 'chosen_sentences_' + lang + '.txt'
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	conn = ssh.connect(hostname=config.host, username=config.user, password=config.password, port=config.port)
	if debug:
		print('Calling:','cd '+ config.remote_folder +'; python3.7 '+ config.server_utils + ' -M ' + str(GET_GOOD_SENTENCES) + ' -l ' + lang + ' -s ' + output_file + ' -wf ' + eflomal_f_alignment_file + ' -wr ' + eflomal_r_alignment_file + ' -c ' + chosen_sent)
	try:
		stdin, stdout, stderr = ssh.exec_command('(cd '+ config.remote_folder +'; python3.7 '+ config.server_utils + ' -M ' + str(GET_GOOD_SENTENCES) + ' -l ' + lang + ' -s ' + output_file + ' -wf ' + eflomal_f_alignment_file + ' -wr ' + eflomal_r_alignment_file + ' -c ' + chosen_sent +')', timeout=10*60)
		print(stderr.readlines(), file=sys.stderr)
		print(stdout.readlines())
	except Exception:
		print("Timeout occurred")
		ssh.connect(hostname=config.host, username=config.user, password=config.password, port=config.port)

	#Retrieves output
	try:
		scp = SCPClient(ssh.get_transport())
		scp.get(config.remote_folder+chosen_sent)
	except SCPException as error:
		print(error)
	ssh.close()

    

#########################################################################################################################


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='master thesis')
	parser.add_argument('-M', '--mode', dest='mode', type=int, default=0, help='function to call')
	parser.add_argument('-d', '--debug', dest='debug', action='store_true', help='enable debug logging')
	parser.add_argument('-l', '--lang', dest='lang', default='iten', help='selected languages: iten, sven or svit')
	parser.add_argument('-o', '--output_file', dest='output_file', default=None, help='selected languages: iten, sven or svit')
	args = parser.parse_args()

	mode = args.mode
	lang = args.lang.strip()
	if args.debug:
		debug = True
	if debug:
		print("Debugging mode:")
	if mode == SETUP_MODE:
		setup(lang)
		if debug:
			print("Setup done")
		call_eflomal(lang)
		if debug:
			print("Eflomal done")
		get_good_sentences(lang)
		if debug:
			print("Sentences done")
	elif mode == BUILD_WORD_ALIGN_CORPUS:
		if args.output_file:
			call_eflomal(lang, args.output_file)
		else:
			call_eflomal(lang)
	elif mode == GET_GOOD_SENTENCES:
		get_good_sentences(lang)
	print("done")