from boto3.session import Session
import sys
import time
import os
if __name__ == "__main__":
    def showError():
        print "wrong number of argument.\n"
        print "the proper synthax is:\n"
        print "application.py <project> <test bundle path> <app path>\n"
        print "for example:\n"
        print "application.py android ./test/test.zip ./build/yoox-dev.apk"



    #==============================================================================
    #
    #                       variables
    #
    #===============================================================================

    projectArn = ""
    devicePoolArn = ""
    testBundleArn = ""
    appArn = ""

    appArnIsReady = False
    testArnIsReady = False

    projectId = ""
    testBundle = ""
    appBundle = ""
    #==============================================================================
    #
    #                       parse CLI arguments:
    #               application.py <project> <test bundle path> <app path>
    #               application.py android ~/test/test.zip ~/build/yoox-dev.apk
    #
    #===============================================================================
    if len(sys.argv) < 2 :
       showError()
    try:
        projectId = "android"
        testBundle = os.environ["ARTIFACTS_DIRECTORY"]+"/tests.zip"
        appBundle = os.environ["ARTIFACTS_DIRECTORY"]+"/yoox-android_DEV.apk"
    except Exception:
        showError()



    #==============================================================================
    #
    #                       Init AWS
    #
    #===============================================================================


    session = Session(aws_access_key_id='AKIAIAFP4BVNZWHBBUZA',
                  aws_secret_access_key='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',
                  region_name='us-west-2')

    #==============================================================================
    #
    #                       Step1: get the project ARN
    #
    #===============================================================================

    deviceFarmClient = session.client("devicefarm")
    response = deviceFarmClient.list_projects()
    for dfProject in response['projects'] :
        if "android" in dfProject['name'] :
            projectArn = dfProject['arn']
            break
    if projectArn == "":
        print "no valid project found"
        sys.exit(0)
    print "project found with ARN: "+projectArn

    #==============================================================================
    #
    #                       Step2: get device pool ARN
    #
    #===============================================================================
    devicePools = deviceFarmClient.list_device_pools(arn=projectArn)
    for dPool in devicePools['devicePools']:
        if dPool['description'] == "Top devices":
            devicePoolArn = dPool['arn']
            break
    if devicePoolArn == "":
        print "No device pool found for the project"
        sys.exit(0)
    print "Device pool ARN is "+ devicePoolArn

    #==============================================================================
    #
    #                       Step3: upload the calabash test bundle
    #
    #===============================================================================
    if testBundle != "":
        print "test size "+ str(os.path.getsize(testBundle))
        uploadTestBundle = deviceFarmClient.create_upload(
                                            projectArn=projectArn,
                                            name=testBundle,
                                            type='CALABASH_TEST_PACKAGE')
        testBundleArn = uploadTestBundle['upload']['arn']
        print "test bundle "+testBundle+"ARN is " +testBundleArn
    else:
        print "wrong test bundle"
        sys.exit(0)

    #==============================================================================
    #
    #                       Step4: upload the calabash test bundle
    #
    #===============================================================================
    if appBundle != "":
        print "bundle size "+ str(os.path.getsize(appBundle))
        bundleType=""
        if ".apk" in appBundle :
            bundleType = "ANDROID_APP"
        else:
            bundleType="IOS_APP"
        uploadTestBundle = deviceFarmClient.create_upload(
                                            projectArn=projectArn,
                                            name=appBundle,
                                            type=bundleType)
        appArn = uploadTestBundle['upload']['arn']
        print "app "+appBundle+" ARN is "+appArn
    else:
        print "wrong app bundle"
        sys.exit(0)


    #
    #==============================================================================
    #
    #                       Step5: wiat foe the app bundle and test bundel to be ready
    #
    #===============================================================================
    max_loop = 10
    currentLoop = 0
    while appArnIsReady is not True and testArnIsReady is not True:
        if testArnIsReady is not True:
            checkTestStatusReq = deviceFarmClient.get_upload(arn=testBundleArn)
            upload = checkTestStatusReq["upload"]
            uploadTestArn = upload['arn']
            uploadTestStatus = upload['status']
            if uploadTestStatus == "SUCCEEDED" and uploadTestArn == testBundleArn:
                print upload
                testBundleArn = True
        if appArnIsReady is not True:
            checkTestStatusReq = deviceFarmClient.get_upload(arn=appArn)
            upload = checkTestStatusReq["upload"]
            uploadAppArn = upload['arn']
            uploadAppStatus = upload['status']
            if uploadAppStatus == "SUCCEEDED" and uploadAppArn == appArn:
                print upload
                testBundleArn = True
        time.sleep(60)
        currentLoop += 1
        if currentLoop >= max_loop:
            break

    #==============================================================================
    #
    #                       Step6: schedule test run
    #
    #===============================================================================
    if  appArnIsReady is True and testArnIsReady is True:
        response = deviceFarmClient.schedule_run(
        projectArn=projectArn,
        appArn=appArn,
        devicePoolArn=devicePoolArn,
        name= projectId+'from ship.io',
        test={
            'type': 'CALABASH',
            'testPackageArn': testBundleArn
            })
        print response
        print "ohoho"
        #here we retrieve the run arn and can use get_run to see the test progress
    else:
         print "issue with checking the artifacts upload status"