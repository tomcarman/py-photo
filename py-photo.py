import os
import json
import exiftool
import csv
import sys
import Tkinter


reload(sys)
sys.setdefaultencoding('utf-8')


root_dir = 'XXX'
target_dir = 'XXX'

file_name_list = []

tags_to_get_list = ['SourceFile', 'FileName', 'Make', 'Model', 'AdjustmentFormatIdentifier', 'Software', 'XResolution', 'YResolution', 'UserComment', 'DeviceModelName', 'MIMEType', 'FileType', 'FileModifyDate', 'VideoCodec', 'QuickTime:MajorBrand']

old_to_new_filename = dict()


my_output = open('python_output.csv', 'w')
writer = csv.writer(my_output)



# ### FOR USE ON FOLDER STRUCTURE

# Loop through folders
for subdir, dirs, files in os.walk(root_dir):
    for file in files:

        # add filenames to an array
        file_name_list.append(os.path.join(subdir, file))

###############################


# FOR USE ON INPUT CSV
# my_input = open('exif_fails_input_1.csv', 'r')
# file_name_list = my_input.read().split('\n')
# my_input.close()


# Run Exiftool instance as context manager - this means terminating the script will terminate any exiftool subprocesses
with exiftool.ExifTool() as et:

    # get exif data for provided list of tags and files, in batch mode
    metadata = et.get_tags_batch(tags_to_get_list, file_name_list)

    # loop through json objects
    for json_object in metadata:

        #if no file name, skip
        if json_object.get('File:FileName') == None:
            continue

        if(json_object.get('File:FileName') == '.DS_Store' or '.ithmb' in json_object.get('SourceFile')): 
            continue # ignore .DS_Store files / iPod thumbnail crap


        new_path = target_dir+'/'

        ###
        # Retrieve FileModifyDate and append yyyy/mm/dd to new_path
        ###

        # if the is a FileModifyDate in the exif data..
        if 'File:FileModifyDate' in json_object:

            # parse out the year, month, day with substrings
            year = json_object.get('File:FileModifyDate')[0:4]
            month = json_object.get('File:FileModifyDate')[5:7]
            day = json_object.get('File:FileModifyDate')[8:10]

            # concatenate to build new path
            new_path = new_path+year+'/'+month+'/'+day+'/'

        else: # FileModifyDate was blank
            new_path = new_path+'Unknown_Date'

        ###
        # Retrieve MIMEType and append to new_path (eg. /videos or /photos)
        ###
        
        if 'File:MIMEType' in json_object:
            media_type = json_object.get('File:MIMEType').partition('/');

            if media_type[0] == 'image':
                new_path = new_path+'photos/'
            elif media_type[0] == 'video':
                new_path = new_path+'videos/'
            # else probably a sidecar preserve in another dir for now
            else:
                new_path = new_path+media_type[0]+'/'

        else: # MIMEType was blank
            new_path = new_path+'Unknown_MIMEType/'

        ###
        # Try and establish device taken with (and do some transformation for common ones)
        ###

        model = ''


        if 'EXIF:Model' in json_object:
            model = json_object.get('EXIF:Model')
        elif 'QuickTime:Model' in json_object:
            model = json_object.get('QuickTime:Model')
        elif 'XML:DeviceModelName' in json_object: 
            model = json_object.get('XML:DeviceModelName')
        elif 'XMP:UserComment' in json_object:
            if(json_object.get('XMP:UserComment') == 'Screenshot'):
                model = 'iPhone Screenshot'

        # Maybe its a file thats been edited on iPhone and lost original EXIF data.
        # Sometimes can be determined by EXIF:Software tag...
        elif 'EXIF:Software' in json_object: 
            software = json_object.get('EXIF:Software')

            if software == 'Instagram':
                model = 'iPhone Edit/Instagram'
            elif software == 'Layout from Instagram':
                model = 'iPhone Edit/Layout'
            elif 'Snapseed' in software:
                model = 'iPhone Edit/Snapseed'
            elif 'VSCO' in software:
                model = 'iPhone Edit/VSCO'

        # Sometime the QuickTime:Software tag is used...
        elif 'QuickTime:Software' in json_object:
            if(json_object.get('QuickTime:Software') == 'Hyperlapse'):
                model = 'Hyperlapse'
            if(json_object.get('QuickTime:Software') == 'Boomerang'):
                model = 'Boomerang'

        # Now some attempt to identify photos received on WhatsApp - !!EXPERIMENTAL!!

        # WhatsApp Received Photo
        elif(json_object.get('EXIF:XResolution') == 72):
            if(json_object.get('EXIF:YResolution') == 72):
                if(json_object.get('File:FileName').startswith('IMG_')):
                    if(json_object.get('File:FileType') == 'JPEG'):
                        model = 'WhatsApp'

        # WhatsApp Received Video
        elif(json_object.get('QuickTime:XResolution') == 72):
            if(json_object.get('QuickTime:YResolution') == 72):
                if(json_object.get('File:FileName').startswith('IMG_')):
                    if(json_object.get('File:FileType') == 'MP4'):
                        model = 'WhatsApp'


        # Else maybe its an Apple Sidecar (eg. slowmo). Really these should be stored in same folder as photo, but for now just isolate
        elif(json_object.get('File:FileType') == 'PLIST'):
            if(json_object.get('PLIST:AdjustmentFormatIdentifier') == 'com.apple.photo'):
                model = 'Apple AAE'





        # Now getting desperate...

        # Older iPhone models didnt use the XMP:UserComment 'Screenshot' tag for screenshots
        # Older whatsapp files didn't meet the matching criteria above...or they might be WeChat received.
        # Trying some other matching criteria, mismatches likely

        elif('iPhone' in json_object.get('SourceFile') or 'iphone' in json_object.get('SourceFile') or 'phone' in json_object.get('SourceFile')):
            if(json_object.get('File:FileName').startswith('IMG_')):
                if(json_object.get('File:FileType') == 'PNG'):
                    # Likely an iphone screenshot...
                    model = 'iPhone Screenshot'
                elif(json_object.get('File:FileType') == 'JPEG'):
                    if(json_object.get('EXIF:XResolution') == 96):
                        if(json_object.get('EXIF:YResolution') == 96):
                            # Likely an old whatsapp received file
                            model = 'WhatsApp'


        # Else maybe a Sony RX100M4 Video file, could result in mismatch..

        elif(json_object.get('QuickTime:MajorBrand') == 'XAVC'):
            if(json_object.get('File:FileType') == 'MP4'):
                model = 'RX100M4'


        # Else maybe a Sony RX100M4 Timelapse file, could result in mismatch..
        
        elif(json_object.get('File:FileType') == 'AVI'):
            if(json_object.get('RIFF:VideoCodec') == 'mjpg'):
                model = 'RX100M4'


        # Basic transformation for common types with obscure names / or mis identified
        if model == 'FC330': # This is Phantom 4 Drone
            model = 'Phantom4'
        elif model == 'DSC-RX100M4':
            model = 'RX100M4'
        elif model == 'FC220': # This is Mavic Pro Drone
            model = 'Mavic Pro'
        elif model == 'LEICA Q (Typ 116)':
            model = 'LEICA Q'
        elif model == 'Canon DIGITAL IXUS i zoom':
            model = 'Canon IXUS'
        elif model == 'Canon DIGITAL IXUS 30':
            model = 'Canon IXUS'
        elif model == 'Canon DIGITAL IXUS 60':
            model = 'Canon IXUS'
        elif model == 'Canon DIGITAL IXUS 850 IS':
            model = 'Canon IXUS'
        elif model == 'Canon EOS 400D DIGITAL':
            model = 'Canon 400D'
        elif model == 'iPhone' and 'EXIF:Software' in json_object and (json_object.get('EXIF:Software') == 'VSCO' or json_object.get('Quicktime:Software') == 'VSCO'): # VSCO writes 'iPhone' as model, want to fix these 
            model = 'iPhone Edit/VSCO'



        # Else cannot identify model...
        elif model == '':
            model = 'Unknown'

        # Append model to file path
        new_path = new_path+model+'/'+json_object.get('File:FileName')


        if 'Unknown' in new_path:
            writer.writerow(['FAIL', json_object.get('SourceFile'), new_path])
        else:
            writer.writerow(['SUCCESS', json_object.get('SourceFile'), new_path])



my_output.close()

