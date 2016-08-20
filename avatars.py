#!/usr/bin/python

import csv, requests, time, os
import json, collections
import mimetypes
import pprint

working_path = './' # Base working path of this script, where everything will be housed

csv_filename = 'images.csv' # Example: 'API_Testing/users_provisioning.csv', relative to
                            # working_path.  This file contains the three  columns needed
                            # by this script.  Those columns are 
                            #   - SIS_user_id 
                            #   
                            #   - image_filename
                            #     the name of the image file, relative to the working path folder
                            #   - image_filetype 
                            #     the filetype of the image.  This will be something like
                            #     jpeg, png, gif. This field is needed right now because
                      
images_path = 'avatars/'  # This is the name of the folder than houses the images.  It
                          # should be relative to the working_path
log_filename = 'log.txt'    # This is the name of the file that will receive all of the
                            # script output 
                            # Example: '/Users/ianm/Documents/Schools/IMU/log.txt',
                            # relative to working_path

domain = 'SOMETHING.instructure.com'
access_token = "YOURTOKENGOESHERE"

##############################################################################
##############################################################################



header = {'Authorization' : 'Bearer {0}'.format(access_token)}

csv_file_reader = csv.DictReader(open(working_path+csv_filename,'rb'))

valid_mimetypes = ('image/jpeg','image/png','image/gif')


log_file = open('{0}{1}'.format(working_path,log_filename),'w+')
def log(str_or_obj):
  st = '{0}'.format(pprint.pformat(str_or_obj))
  log_file.write(st)
  log_file.write("\n")
  print(st)
  

for user_image in csv_file_reader:
  file_id = None

  # Step 1: Start upload file to user's file storage in Canvas
  inform_api_url = "https://{domain}/api/v1/users/self/files".format(domain=domain)
  image_path = '{0}{1}{2}'.format(working_path,images_path,user_image['image_filename'])
  mime_type,encoding = mimetypes.guess_type(image_path)

  if not mime_type in valid_mimetypes:
    log('Not a valid mimetype: {0}'.format(mime_type))
    continue
  inform_parameters = {
    'name':user_image['image_filename'],
    'size':os.path.getsize(image_path), # read the filesize
    'content_type':mime_type,
    'parent_folder_path':'profile pictures',
    'as_user_id':'sis_user_id:{0}'.format(user_image['user_id'])
     }
  res = requests.post(inform_api_url,headers=header,data=inform_parameters)

  log("Done prepping Canvas for upload, now sending the data...")
  json_res = json.loads(res.text,object_pairs_hook=collections.OrderedDict)

  # Step 2:  Upload data
 
  files = {'file':open(image_path,'rb').read()}
  
  _data = json_res.items()
  _data[1] = ('upload_params',_data[1][1].items())

  log("Yes! Done sending pre-emptive 'here comes data' data, now uploading the file...")
  upload_file_response = requests.post(json_res['upload_url'],data=_data[1][1],files=files,allow_redirects=False)

  # Step 3: Confirm upload

  log("Done uploading the file, now confirming the upload...")
  confirmation = requests.post(upload_file_response.headers['location'],headers=header)

  if 'id' in confirmation.json():
    file_id = confirmation.json()['id'] 
  else:
    print 'no id here'
    pprint(confirmation.json())
  log("upload confirmed...nicely done!")

  # Make api call to set avatar image to the token of the uploaded imaged (file_id)
  params = { 'as_user_id':'sis_user_id:{0}'.format(user_image['user_id'])}
  avatar_options = requests.get("https://%s/api/v1/users/sis_user_id:%s/avatars"%(domain,'{0}'.format(user_image['user_id'])),headers=header,params=params)
  for ao in avatar_options.json():
    #print ao.keys()
    if ao.get('display_name')==user_image['image_filename']:
      log("avatar option found...")
      log((ao.get('display_name'),ao.get('token'), ao.get('url')))
      params['user[avatar][token]'] = ao.get('token')

      set_avatar_user = requests.put("https://%s/api/v1/users/sis_user_id:%s"%(domain,'{0}'.format(user_image['user_id'])),headers=header,params=params)
      if set_avatar_user.status_code == 200:
        log('success uploading user avatar for {0}'.format(user_image['user_id']))
      #pprint(set_avatar_user)


  #pprint(avatar_options.json())

