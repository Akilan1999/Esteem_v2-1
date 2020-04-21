import flask
from flask import jsonify

application = flask.Flask(__name__)
application.config["DEBUG"] = True

# Create some test data for our catalog in the form of a list of dictionaries.

Devices = [
{
        'DeviceName': 'LightPanel1',
        'DeviceModel': 'Amazing Lights',
        'ElecConsp': 0.08,
        'CurConsp': 0.08,
        'status': 'on',
        'ip_address': '127.0.0.200'
    },
{
        'DeviceName': 'LightPanel2',
        'DeviceModel': 'Amazing Lights',
        'ElecConsp': 0.081,
        'CurConsp': 0.081,
        'status': 'on',
        'ip_address': '127.0.0.201'
    },
{
        'DeviceName': 'LightPanel3',
        'DeviceModel': 'Amazing Lights',
        'ElecConsp': 0.08,
        'CurConsp': 0.08,
        'status': 'on',
        'ip_address': '127.0.0.202'
    },
{
        'DeviceName': 'LightPanel4',
        'DeviceModel': 'Amazing Lights',
        'ElecConsp': 0.08,
        'CurConsp': 0.08,
        'status': 'on',
        'ip_address': '127.0.0.203'
    },
{
        'DeviceName': 'LightPanel5',
        'DeviceModel': 'Amazing Lights',
        'ElecConsp': 0.08,
        'CurConsp': 0.08,
        'status': 'on',
        'ip_address': '127.0.0.204'
    },
{
        'DeviceName': 'LightPanel6',
        'DeviceModel': 'Amazing Lights',
        'ElecConsp': 0.1,
        'CurConsp': 0.1,
        'status': 'on',
        'ip_address': '127.0.0.205'
    },
{
        'DeviceName': 'LightPanel7',
        'DeviceModel': 'Amazing Lights',
        'ElecConsp': 0.06,
        'CurConsp': 0.06,
        'status': 'on',
        'ip_address': '127.0.0.206'
    },
    {
        'DeviceName': 'LedBulb1',
        'DeviceModel': 'Amazing Lights',
        'ElecConsp': 0.03,
        'CurConsp': 0.03,
        'status': 'on',
        'ip_address': '127.0.0.210'
    },
{
        'DeviceName': 'LedBulb2',
        'DeviceModel': 'Amazing Lights',
        'ElecConsp': 0.03,
        'CurConsp': 0.03,
        'status': 'on',
        'ip_address': '127.0.0.211'
    },
{
        'DeviceName': 'LedBulb3',
        'DeviceModel': 'Amazing Lights',
        'ElecConsp': 0.03,
        'CurConsp': 0.03,
        'status': 'on',
        'ip_address': '127.0.0.212'
    },
    {
        'DeviceName': 'Lamp1',
        'DeviceModel': 'Amazing Lights',
        'ElecConsp': 0.06,
        'CurConsp': 0.06,
        'status': 'on',
        'ip_address': '127.0.0.2'
    },
    {
        'DeviceName': 'Lamp2',
        'DeviceModel': 'Amazing Lights',
        'ElecConsp': 0.03,
        'CurConsp': 0.03,
        'status': 'on',
        'ip_address': '127.0.0.3'
    },
{
        'DeviceName': 'Lamp3',
        'DeviceModel': 'Amazing Lights',
        'ElecConsp': 0.04,
        'CurConsp': 0.04,
        'status': 'on',
        'ip_address': '127.0.0.31'
    },
{
        'DeviceName': 'Lamp4',
        'DeviceModel': 'Amazing Lights',
        'ElecConsp': 0.018,
        'CurConsp': 0.018,
        'status': 'on',
        'ip_address': '127.0.0.32'
    },
{
        'DeviceName': 'Lamp5',
        'DeviceModel': 'Amazing Lights',
        'ElecConsp': 0.05,
        'CurConsp': 0.05,
        'status': 'on',
        'ip_address': '127.0.0.33'
    },
    {
        'DeviceName': 'Fridge1',
        'DeviceModel': 'Amazing Cooling',
        'ElecConsp': 0.13,
        'CurConsp': 0.13,
        'status': 'on',
        'ip_address': '127.0.0.4'
    },
    {
        'DeviceName': 'Fridge2',
        'DeviceModel': 'Amazing Cooling',
        'ElecConsp': 0.21,
        'CurConsp': 0.21,
        'status': 'on',
        'ip_address': '127.0.0.5'
    },
    {
        'DeviceName': 'Tv1',
        'DeviceModel': 'Amazing Entertainment',
        'ElecConsp': 0.07,
        'CurConsp': 0.07,
        'status': 'on',
        'ip_address': '127.0.0.6'
    },
    {
        'DeviceName': 'Tv2',
        'DeviceModel': 'Amazing Entertainment',
        'ElecConsp': 0.1,
        'CurConsp': 0.1,
        'status': 'on',
        'ip_address': '127.0.0.7'
    },
{
        'DeviceName': 'Tv3',
        'DeviceModel': 'Amazing Entertainment',
        'ElecConsp': 0.09,
        'CurConsp': 0.09,
        'status': 'on',
        'ip_address': '127.0.0.71'
    },
    {
        'DeviceName': 'Ac1',
        'DeviceModel': 'Amazing Cooling',
        'ElecConsp': 0.98,
        'CurConsp': 0.98,
        'status': 'on',
        'ip_address': '127.0.0.8'
    },
{
        'DeviceName': 'Ac2',
        'DeviceModel': 'Amazing Cooling',
        'ElecConsp': 1.25,
        'CurConsp': 1.25,
        'status': 'on',
        'ip_address': '127.0.0.81'
    },
{
        'DeviceName': 'CoffeeMaker',
        'DeviceModel': 'Amazing Coffee',
        'ElecConsp': 0.05,
        'CurConsp': 0.05,
        'status': 'on',
        'ip_address': '127.0.0.9'
    },
{
        'DeviceName': 'MicrowaveOven',
        'DeviceModel': 'Amazing Oven',
        'ElecConsp': 0.2,
        'CurConsp': 0.2,
        'status': 'on',
        'ip_address': '127.0.0.91'
    },
{
        'DeviceName': 'KitchenChimney',
        'DeviceModel': 'Amazing Chimney',
        'ElecConsp': 0.3,
        'CurConsp': 0.3,
        'status': 'on',
        'ip_address': '127.0.0.92'
    },

{
        'DeviceName': 'Xbox OneX',
        'DeviceModel': 'Amazing Gaming',
        'ElecConsp': 0.09,
        'CurConsp': 0.09,
        'status': 'on',
        'ip_address': '127.0.0.93'
    },
{
        'DeviceName': 'HomeTheatre',
        'DeviceModel': 'Amazing Entertainment1',
        'ElecConsp': 0.098,
        'CurConsp': 0.098,
        'status': 'on',
        'ip_address': '127.0.0.94'
    },
{
        'DeviceName': 'WashingMachine',
        'DeviceModel': 'Amazing washing',
        'ElecConsp': 0.28,
        'CurConsp': 0.28,
        'status': 'on',
        'ip_address': '127.0.0.98'
    },
{
        'DeviceName': 'Desktop1',
        'DeviceModel': 'Amazing Computer',
        'ElecConsp': 0.17,
        'CurConsp': 0.17,
        'status': 'on',
        'ip_address': '127.0.0.96'
    },
{
        'DeviceName': 'Dishwasher',
        'DeviceModel': 'Amazing Dishwashish',
        'ElecConsp': 0.2,
        'CurConsp': 0.2,
        'status': 'on',
        'ip_address': '127.0.0.99'
    },
{
        'DeviceName': 'VacuumCleaner1',
        'DeviceModel': 'Amazing vacuuming',
        'ElecConsp': 0.8,
        'CurConsp': 0.8,
        'status': 'on',
        'ip_address': '127.0.0.110'
    },
{
        'DeviceName': 'CeilingFan1',
        'DeviceModel': 'Amazing cooling fan',
        'ElecConsp': 0.08,
        'CurConsp': 0.08,
        'status': 'on',
        'ip_address': '127.0.0.121'
    },
{
        'DeviceName': 'CeilingFan2',
        'DeviceModel': 'Amazing cooling fan',
        'ElecConsp': 0.085,
        'CurConsp': 0.085,
        'status': 'on',
        'ip_address': '127.0.0.122'
    },{
        'DeviceName': 'CeilingFan3',
        'DeviceModel': 'Amazing cooling fan',
        'ElecConsp': 0.06,
        'CurConsp': 0.06,
        'status': 'on',
        'ip_address': '127.0.0.123'
    },{
        'DeviceName': 'CeilingFan4',
        'DeviceModel': 'Amazing cooling fan',
        'ElecConsp': 0.07,
        'CurConsp': 0.07,
        'status': 'on',
        'ip_address': '127.0.0.124'
    },{
        'DeviceName': 'CeilingFan5',
        'DeviceModel': 'Amazing cooling fan',
        'ElecConsp': 0.08,
        'CurConsp': 0.08,
        'status': 'on',
        'ip_address': '127.0.0.121'
    },{
        'DeviceName': 'CeilingFan6',
        'DeviceModel': 'Amazing cooling fan',
        'ElecConsp': 0.08,
        'CurConsp': 0.08,
        'status': 'on',
        'ip_address': '127.0.0.121'
    },
{
        'DeviceName': 'Iron',
        'DeviceModel': 'Amazing ironing',
        'ElecConsp': 0.97,
        'CurConsp': 0.97,
        'status': 'on',
        'ip_address': '127.0.0.131'
    },
{
        'DeviceName': 'HairDryer',
        'DeviceModel': 'Amazing hair drying',
        'ElecConsp': 1.2,
        'CurConsp': 1.2,
        'status': 'on',
        'ip_address': '127.0.0.141'
    },

]



# Used to turn on and off any device
@application.route('/api/changestatus/<string:device_id>', methods=['GET'])
def api_status(device_id):
    get_device = next(item for item in Devices if item["DeviceName"] == device_id)

    if get_device:
        get_device['status'] = 'on' if get_device['status'] == 'off' else 'off'
        get_device['CurConsp'] = 0 if get_device['CurConsp'] == get_device['ElecConsp'] else get_device['ElecConsp']
        return jsonify(Devices)

    return jsonify('No device exsists with this id')


@application.route('/api/alldevicesconsumption/', methods=['GET'])
def total_consumption():
    return jsonify(Devices)


application.run()
