"""
===========================================================================
Authon       :  Aastha
Created on   :  19-09-2024
Purpose      :  Standardise the codings
Modified on  :  
M.Purpose    :  
Version      :  1.0
===========================================================================
"""
import base64
from datetime import datetime
import cv2
import requests
from DB import *
#-----------------------------------------------------------------------------------------------------------------------
# Get the project details
#-----------------------------------------------------------------------------------------------------------------------
df_prj = None
sql = "exec vision_get_details"
df_prj = mssql_read_data(sql)
project_id = "10"
# current_time = datetime.datetime.now()
#-----------------------------------------------------------------------------------------------------------------------
def SaveImage_Jig(img_str,location,img_dir):
    try: 
        url = "http://10.121.3.141/istore/sso.asmx" # D:\OneDrive - TVS Motor Company Ltd\wwwroot\SSO_Bckp_Srvr
        API =  "kMImXTti1r1rWfaPN8cuDA=="
        API_ENDPOINT = url
        datas = '<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><SaveImage_JigN xmlns="http://tempuri.org/"><base64image>'+ img_str +'</base64image><location>'+ location +'</location><img_dir>'+ img_dir +'</img_dir><API_KEY>'+ API +'</API_KEY></SaveImage_JigN></soap:Body></soap:Envelope>'
        header = {'Content-Type':'text/xml;','Cache-Control': 'no-cache'}
        # sending post request and saving response as response object 
        r = requests.post(url = API_ENDPOINT, data = datas, headers=header)
        pastebin_url = r.text.replace('<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Body><SaveImage_JigNResponse xmlns="http://tempuri.org/"><SaveImage_JigNResult>','').replace('</SaveImage_JigNResult></SaveImage_JigNResponse></soap:Body></soap:Envelope>','')
        print('Image Stored')
    except Exception as ee:
        print('Save Image: '+str(ee))
# def Detect_V8(frame, model, predicted_frame):
    # Your existing code here for object detection
    # Make sure to use 'predicted_frame' within this function
 
    # return output_list, bbox, conf, predicted_frame
#-----------------------------------------------------------------------------------------------------------------------
def Store_Image(project_id,rslt_sts,frame,body,remarks,dbu=True,send_mail=True):
    try:
 
        #--------------------------------------------------------------------------------
        # Fetch project details based on the project ID
        print("project id",project_id)
        # print(df_prj)
        # print(df_prj.shape)
        # print(list(df_prj.columns))
        proj_det = df_prj[df_prj['project_id'] == project_id]
        # print(proj_det.shape)
        # print(proj_det.shape[0])
        #--------------------------------------------------------------------------------
        if proj_det.shape[0] > 0:
            global pframe
            plant = proj_det['plant'].values[0]
            loc = proj_det["loc"].values[0]
            area = proj_det["line_name"].values[0]
            project_title = proj_det["project_title"].values[0]
            project_dir = proj_det["project_dir"].values[0]
            user_mid = proj_det["user_mid"].values[0]
            #print(user_mid)
            mail_subject = proj_det["mail_subject"].values[0]
            #print(plant,loc,area,project_title,project_dir,user_mid,mail_subject)
            # predicted_frame = obj_detection.Detect_V8()
            if frame is not None:
                project_dir_str = str(project_dir)
                # Debugging step to see what type project_dir is
                #print(f"project_dir (type: {type(project_dir)}):", project_dir)

                
                filename = str(project_dir) + '_'+  str(datetime.now().strftime("%d_%m_%Y_%H_%M_%S"))
                #print("filename :",filename)
		#filename = str(project_dir) + '_' + datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
 
                if dbu: # If database updation required or not
                    #print(f"plant :{plant}",type(plant),f"loc :{loc}", type(loc),f"area :{area}",type(area),f"project_title : {project_title}",type(project_title),f"filename : {filename}",type(filename),f"rslt_sts : {rslt_sts}",type(rslt_sts),f"project_id : {str(project_id)} =",type(project_id), f"remarks : {remarks} =",type(remarks))
                    sql = "set dateformat dmy;EXEC store_vision_efficency @plant='"+ str(plant) +"',@loc='"+ loc +"',@area='"+ area +"',@pro_title='"+ project_title +"',@Img_filename='"+ filename +"',@result='"+ rslt_sts +"',@project_id='"+str(project_id)+"',@remarks='"+ remarks +"';"
                    #print(sql)
                    mssql_insert_data(sql)
                     
                    retval , buffer = cv2.imencode('.jpg',frame)
                    encoded_string = base64.b64encode(buffer).decode('utf-8')
 
                try:
                    # Save image into the server
                    SaveImage_Jig(encoded_string, str(filename),project_dir)
                    if send_mail:
                        # Send notification mail to the end user
                        alert(user_mid,mail_subject,body,encoded_string)
                except Exception as e:
                    print('Image Save Exception: ', e)
        else:
            # Project details are missing in the database
            alert("tvsglobalone@tvsmotor.com","Project details are missing for the project ID :" + project_id,"Project details are missing for the project ID :" + project_id,None)
 
    except Exception as ee:
        print("Exception in Store_Image:",str(ee))
#-----------------------------------------------------------------------------------------------------------------------
def alert(TO_Mail,Subject,Body,encoded_string):
    # url = "http://10.121.2.122:6003/send_mail" 
    url = "http://10.121.2.195:6000/send_mail" 
 
    # ##Image Save
    # retval , buffer = cv2.imencode('.jpg',image_data)
    # encoded_string = base64.b64encode(buffer).decode('utf-8')
 
    data = {
        "to_address": TO_Mail,
        "subject": Subject,
        "body": Body,
        "image" : encoded_string
    }
 
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print("Email sent successfully at Project ID: " + {project_id}) 
        else:
            print("Failed to send email. Status code:", response.status_code)
    except Exception as e:
        print("Error:", str(e))
#===================================================================================================================
 
