*** Settings ***
Library         BuiltIn
Library         Selenium2Library  timeout=5  implicit_wait=1
Library         String
Resource        keywords.txt
Resource        plone/app/robotframework/selenium.robot
Resource        plone/app/robotframework/server.robot
Resource        plone/app/robotframework/annotate.robot
Library         Remote  ${PLONEURL}/RobotRemote
Variables       plone/app/testing/interfaces.py
Variables       bika/lims/tests/variables.py

Suite Setup     Start browser
Suite Teardown  Close All Browsers

Library          DebugLibrary



*** Variables ***

${input_identifier} =  input#arimport_file

*** Test Cases ***

Importing invalid filename fails

A perfect AR
    #Log in   test_labmanager  test_labmanager
    Log in   admin  secret
    setup stuff

    load arimport_perfect.csv
    There should be no errors
    There should be 4 ARs

An AR with errors, imports correctly after we fix them
    Log in  test_labmanager  test_labmanager
    setup stuff

    load arimport_missing_Sample Type.csv
    the Sample Type field value should be ''
    an error containing Sample Type should exist
    select from dropdown   Sample Type        Sample Type 1
    click button      Save
    run validate transition
    There should be no errors
    run import transition
    There should be 4 ars

*** Keywords ***

setup stuff
    ${client_uid} =  Create Object   clients  Client  c01   title=Client 1 Title  ClientID=Client 1 ID
    ${contact_uid} =  Create Object   clients/c01   Contact   contact1   title=Contact 1
    ${cat_uid} =  Create Object  bika_setup/bika_analysiscategories  AnalysisCategory  c1  title=Category 1
    ${st_uid} =  Create Object   bika_setup/bika_sampletypes  SampleType  ST1  title=Sample Type 1   Prefix=ST
    ${sp_uid} =  Create Object   bika_setup/bika_samplepoints  SamplePoint  SP1  title=Sample Point 1
    ${service_uid1} =  Create Object  bika_setup/bika_analysisservices  AnalysisService  srv1  title=Service 1 Title  Keyword=srv1  Category=${cat_uid}
    ${service_uid2} =  Create Object  bika_setup/bika_analysisservices  AnalysisService  srv2  title=Service 2 Title  Keyword=srv2  Category=${cat_uid}
    ${service_uid3} =  Create Object  bika_setup/bika_analysisservices  AnalysisService  srv3  title=Service 3 Title  Keyword=srv3  Category=${cat_uid}
    ${profile_uid1} =  Create Object  bika_setup/bika_analysisprofiles  AnalysisProfile  prf1  title=Profile 1 Title  Service=${service_uid1},${service_uid1}

load ${filename}
    Go to                       http://localhost:55001/plone/clients/c01
    Wait until page contains    Imports
    click link                  Imports
    Wait until page contains    AR Import
    click link                  AR Import
    ${PATH_TO_TEST} =           run keyword   resource_filename
    Choose File                 css=${input_identifier}  ${PATH_TO_TEST}/files/${filename}

    Set Selenium Timeout        10
    Click Button                Import
    Set Selenium Timeout        5

There should be no errors
    debug
    Textfield value should be  css=#errors  ''
    State of arimport is Valid

State should be ${state_id}
    Page should contain element  css=span.state-${state_id}

run ${transition} transition
    # plone workflow dropdown
    Click Element  css=a[title="Change the state of this item"]
    Click Element  workflow-transition-validate

There should be ${nr} ARs
    debug

the ${field} value should be ${y}
    debug
    element value should be  ${y}
