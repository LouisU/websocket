from scapy.all import *
from queue import Queue
from threading import Thread
import psutil
import platform
import traceback
import json
import datetime
import requests
import time
import sys

class capture(object):
    def __init__(self,test_object, task_id):
        self.test_object = test_object
        self.task_id = task_id
        self.save_interval = 300
        self.os = platform.platform().split('-')[0]
        self.iface, self.client_ip = self.get_net_ifc()
        print(self.iface)
        self.q = Queue()
        self.thread_num = 10
        self.webex_server_location = {}

    def get_webex_server_geo(self, ip):
        resp = json.loads(
            requests.get('http://api.ipapi.com/api/%s?access_key=9a7e0dc5e65b65c583e3c6a2acb2e445' % ip).content)
        country = resp['country_name']
        return (country)


    def get_dscp_code(self, tos_code):
        dscp = '0'
        cos = 'unknow'
        tos_dscp_mapping = {
            '0': 'CS0', '32': 'CS1', '40': 'AF11', '48': 'AF12', '56': 'AF13',
            '64': 'CS2', '72': 'AF21', '80': 'AF22', '88': 'AF23', '96': 'CS3',
            '104': 'AF31', '112': 'AF32', '120': 'AF33', '128': 'CS4', '136': 'AF41',
            '144': 'AF42', '152': 'AF43', '160': 'CS5', '184': 'EF', '192': 'CS6', '224': 'CS7'
        }

        cos_mapping = {
            'EF': 'Class 1',
            'AF31': 'Class 2',
            'AF41': 'Class 2v',
            'AF21': 'Class 3',
            'AF11': 'Scavenger',
            'BE': 'Class4'
        }
        if str(tos_code) in tos_dscp_mapping.keys():
            dscp = tos_dscp_mapping[str(tos_code)]
        if dscp in cos_mapping.keys():
            cos = cos_mapping[dscp]
        return dscp, cos


    def get_webex_cpu_usage(self):
        listOfProcObjects = []
        webex_cpu_usage = 0
        webex_mem_usage = 0
        for proc in psutil.process_iter():
            try:
                if self.os == 'Windows':
                    if proc.name() == 'webexmta.exe' or proc.name() == 'atmgr.exe':
                        pinfo = proc.as_dict(attrs=['pid', 'name', 'username'])
                        pinfo['cpu'] = proc.cpu_percent()
                        pinfo['mem'] = proc.memory_percent()
                        listOfProcObjects.append(pinfo);
                        webex_cpu_usage += pinfo['cpu']
                        webex_mem_usage += pinfo['mem']
                elif self.os == 'Darwin':
                    if proc.name() == 'Cisco Webex Meetings' or proc.name() == 'Meeting Center' or proc.name() == 'webexmta' or proc.name() == 'webexpluginagent':
                        pinfo = proc.as_dict(attrs=['pid', 'name', 'username'])
                        pinfo['cpu'] = proc.cpu_percent()
                        pinfo['mem'] = proc.memory_percent()
                        listOfProcObjects.append(pinfo);
                        webex_cpu_usage += pinfo['cpu']
                        webex_mem_usage += pinfo['mem']
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        listOfProcObjects = sorted(listOfProcObjects, key=lambda procObj: procObj['mem'], reverse=True)
        return (webex_cpu_usage, webex_mem_usage)


    def get_net_ifc(self):
        if self.os == 'Darwin' or self.os == 'Linux':
            netcard_info = []
            info = psutil.net_if_addrs()
            for k, v in info.items():
                for item in v:
                    if item[0] == 2:
                        netcard_info.append((k, item[1]))
            for ifc in netcard_info:
                if ifc[1].startswith('9.'):
                    return (ifc[0], ifc[1])
            return ('error', 'error')

        elif self.os == 'Windows':
            int_list = str(IFACES).split('\n')
            int_list2 = []
            client_ip = 'unknow'
            for i in range(len(int_list)):
                if i == 0:
                    continue
                else:
                    temp_list = int_list[i].split('  ')
                    list1 = temp_list[:]
                    for j in range(len(temp_list)):
                        if j == 0:
                            del list1[0]
                        if temp_list[j] == '':
                            list1.remove('')
                    int_list2.append(list1)
            int_list3 = []
            for k in int_list2:
                try:
                    if k[1].strip().startswith('9.'):
                        client_ip = k[1].strip()
                        int_list3.append(k[0].strip())
                except:
                    continue
            if len(int_list3) == 2:
                return (int_list3[1], client_ip)
            return (int_list3[0], client_ip)


    def packet_capture(self):
        sniff(iface=self.iface, filter='udp', prn=lambda packet: self.q.put(packet), store=0)


    def output_payload_all(self, payload):
        output = ''
        pos = 0
        row = 0
        output += str(row) + '\t'
        for i in range(len(payload)):
            x = payload[i]
            if pos == 3:
                row += 1
                output += hex(x)
                if i < len(payload) - 1:
                    output += '\n' + str(row) + '\t'
                pos = 0


            else:

                output += hex(x) + '\t'
                pos += 1
        return (output)


    def output_payload_row(self, payload, row, length=4):
        output = 'row\t'

        for i in range(row * length, (row + 1) * length):
            output += hex(payload[i]) + '\t'
        return (output)


    def validate_rtcp(self, payload, position):
        if payload[position + 0] > 128 and payload[position + 0] < 176 and payload[position + 1] >= 200 and payload[
            position + 1] <= 206:
            return True
        else:
            return False


    def analysis_packet(self):
        rtcp_packets = []
        rtcp_audio_send = []
        rtcp_audio_receive = []
        rtcp_video_send = []
        rtcp_video_receive = []
        webex_udp_data_octecs_send = 0
        webex_udp_data_octecs_receive = 0
        time1 = time.time()
        total_udp_packets = 0
        total_udp_data_octecs = 0
        total_rtcp_packets = 0
        total_rtcp_data_octecs = 0
        rtp_type = {}
        content_type = {}
        pt_list = ['SR', 'RR', 'SDES', 'BYE', 'APP', 'Unknown', 'Payload-specific Feedback']
        chunk_item_type_list = ['n/a', 'CNAME', 'NAME', 'EMAIL', 'PHONE', 'LOC', 'TOOL', 'NOTE', 'PRIV']
        iii = 0
        get_audio_port = False
        get_video_port = False
        while True:
            if not self.q.empty():
                # print(q.qsize())
                packet = self.q.get()
                result = {}
                try:
                    result['TOS'] = packet['IP'].tos
                    result['protocol'] = packet['IP'].proto
                    result['src_ip'] = packet['IP'].src
                    result['dst_ip'] = packet['IP'].dst
                    result['src_port'] = packet['UDP'].sport
                    result['dst_port'] = packet['UDP'].dport
                    result['udp_data_len'] = packet['UDP'].len - 8
                    result['udp_data_payload'] = bytes(packet['UDP'].payload)
                    payload = result['udp_data_payload']
                except:
                    continue
                if iii == 0:
                    if (result['src_ip'].startswith('9.')) and (not result['dst_ip'].startswith('9.')):
                        self.webex_server_location[result['dst_ip']] = self.get_webex_server_geo(result['dst_ip'])
                        iii += 1
                    elif (not result['dst_ip'].startswith('9.')) and (result['src_ip'].startswith('9.')):
                        self.webex_server_location[result['dst_ip']] = self.get_webex_server_geo(result['src_ip'])
                        iii += 1
                if result['src_port'] == 9000:
                    webex_udp_data_octecs_receive += (result['udp_data_len'] + 28)
                elif result['dst_port'] == 9000:
                    webex_udp_data_octecs_send += (result['udp_data_len'] + 28)
                total_udp_packets += 1
                total_udp_data_octecs += result['udp_data_len']

                if payload[1] in rtp_type.keys():
                    rtp_type[payload[1]] += 1
                else:
                    rtp_type[payload[1]] = 1

                i = 0

                if not get_audio_port:
                    if payload[1] == 101:
                        if result['src_port'] == 9000:
                            content_type[result['dst_port']] = 'audio'
                        else:
                            content_type[result['src_port']] = 'audio'
                        get_audio_port = True
                if not get_video_port:
                    if payload[1] == 226:
                        if result['src_port'] == 9000:
                            content_type[result['dst_port']] = 'video'
                        else:
                            content_type[result['src_port']] = 'video'
                        get_video_port = True
                if self.test_object == 'jabber':
                    if result['src_port']==9000 or result['dst_port']==9000:
                        continue
                if self.validate_rtcp(payload, 0):  # valid rtcp packet
                    content = 'unknow'
                    if result['dst_port'] in content_type.keys():
                        content = content_type[result['dst_port']]
                    elif result['src_port'] in content_type.keys():
                        content = content_type[result['src_port']]
                    result['content_type'] = content
                    total_rtcp_packets += 1
                    total_rtcp_data_octecs += result['udp_data_len']
                    packet_percentage = 100 * total_rtcp_packets / total_udp_packets
                    result['rtcp_compound'] = []
                    row4B = 0
                    idx = 0
                    while row4B * 4 < result['udp_data_len']:
                        if self.validate_rtcp(payload, row4B * 4) == False or result['udp_data_len'] - row4B * 4 < payload[
                            row4B * 4 + 2] * 256 + payload[row4B * 4 + 3] or result['udp_data_len'] - row4B * 4 == 16:
                            # the rest of packet has less bytes than the number in the length bit
                            length = result['udp_data_len'] - row4B * 4
                            idx_B = row4B * 4
                            raw_data = []

                            while idx_B <= result['udp_data_len'] - 1:
                                raw_data.append(payload[idx_B])
                                idx_B += 1

                            result['rtcp_compound'].append(
                                {'raw_data': raw_data, 'RTCP_payload_type': 'non_rtcp', 'length': length})
                            break
                        result['rtcp_compound'].append({})
                        result['rtcp_compound'][-1]['RTCP_payload_type'] = pt_list[payload[row4B * 4 + 1] - 200]
                        if result['rtcp_compound'][-1]['RTCP_payload_type'] == 'SR' or result['rtcp_compound'][-1][
                            'RTCP_payload_type'] == 'RR':
                            try:
                                result['rtcp_compound'][-1]['RTP_reception_report_count'] = payload[row4B * 4 + 0] - 128
                                result['rtcp_compound'][-1]['SR_RR_report_length'] = payload[row4B * 4 + 2] * 256 + payload[
                                    row4B * 4 + 3]
                                # print(output_payload_row(payload,row4B))
                                row4B += 1  # new 32bit row

                                result['rtcp_compound'][-1]['RTCP_sender_SSRC'] = payload[row4B * 4 + 0] * 256 * 256 * 256 + \
                                                                                  payload[row4B * 4 + 1] * 256 * 256 + \
                                                                                  payload[row4B * 4 + 2] * 256 + payload[
                                                                                      row4B * 4 + 3]
                                # print(output_payload_row(payload,row4B))
                                row4B += 1  # new 32bit row

                                if result['rtcp_compound'][-1]['RTCP_payload_type'] == 'SR':
                                    result['rtcp_compound'][-1]['RTCP_timestamp_msw'] = payload[
                                                                                            row4B * 4 + 0] * 256 * 256 * 256 + \
                                                                                        payload[row4B * 4 + 1] * 256 * 256 + \
                                                                                        payload[row4B * 4 + 2] * 256 + \
                                                                                        payload[row4B * 4 + 3]
                                    # print(output_payload_row(payload,row4B))
                                    row4B += 1  # new 32bit row

                                    result['rtcp_compound'][-1]['RTCP_timestamp_lsw'] = payload[
                                                                                            row4B * 4 + 0] * 256 * 256 * 256 + \
                                                                                        payload[row4B * 4 + 1] * 256 * 256 + \
                                                                                        payload[row4B * 4 + 2] * 256 + \
                                                                                        payload[row4B * 4 + 3]
                                    # print(output_payload_row(payload,row4B))
                                    row4B += 1  # new 32bit row

                                    result['rtcp_compound'][-1]['RTCP_timestamp_rtp'] = payload[
                                                                                            row4B * 4 + 0] * 256 * 256 * 256 + \
                                                                                        payload[row4B * 4 + 1] * 256 * 256 + \
                                                                                        payload[row4B * 4 + 2] * 256 + \
                                                                                        payload[row4B * 4 + 3]
                                    # print(output_payload_row(payload,row4B))
                                    row4B += 1  # new 32bit row

                                    result['rtcp_compound'][-1]['RTCP_sender_packet_count'] = payload[
                                                                                                  row4B * 4 + 0] * 256 * 256 * 256 + \
                                                                                              payload[
                                                                                                  row4B * 4 + 1] * 256 * 256 + \
                                                                                              payload[row4B * 4 + 2] * 256 + \
                                                                                              payload[row4B * 4 + 3]
                                    # print(output_payload_row(payload,row4B))
                                    row4B += 1  # new 32bit row

                                    result['rtcp_compound'][-1]['RTCP_sender_row4Btec_count'] = payload[
                                                                                                    row4B * 4 + 0] * 256 * 256 * 256 + \
                                                                                                payload[
                                                                                                    row4B * 4 + 1] * 256 * 256 + \
                                                                                                payload[
                                                                                                    row4B * 4 + 2] * 256 + \
                                                                                                payload[row4B * 4 + 3]
                                    # print(output_payload_row(payload,row4B))
                                    row4B += 1  # new 32bit row
                                result['rtcp_compound'][-1]['RTCP_reception_report_list'] = []
                                for i in range(result['rtcp_compound'][-1]['RTP_reception_report_count']):
                                    rr = {}

                                    rr['SSRC'] = payload[row4B * 4 + 0] * 256 * 256 * 256 + payload[
                                        row4B * 4 + 1] * 256 * 256 + payload[row4B * 4 + 2] * 256 + payload[row4B * 4 + 3]
                                    # print(output_payload_row(payload,row4B))
                                    row4B += 1  # new 32bit row
                                    rr['fraction_lost'] = payload[row4B * 4 + 0]
                                    rr['cumulative_lost'] = payload[row4B * 4 + 1] * 256 * 256 + payload[
                                        row4B * 4 + 1] * 256 + payload[row4B * 4 + 3]
                                    # print(output_payload_row(payload,row4B))
                                    row4B += 1  # new 32bit row
                                    rr['highest_sequence'] = payload[row4B * 4 + 0] * 256 * 256 * 256 + payload[
                                        row4B * 4 + 1] * 256 * 256 + payload[row4B * 4 + 2] * 256 + payload[row4B * 4 + 3]
                                    # print(output_payload_row(payload,row4B))
                                    row4B += 1  # new 32bit row
                                    if self.test_object == 'webex':
                                        rr['jitter'] = (payload[row4B * 4 + 0] * 256 * 256 * 256 + payload[
                                            row4B * 4 + 1] * 256 * 256 + payload[row4B * 4 + 2] * 256 + payload[
                                                            row4B * 4 + 3]) / 48
                                    elif self.test_object == 'jabber':
                                        rr['jitter'] = (payload[row4B * 4 + 0] * 256 * 256 * 256 + payload[
                                            row4B * 4 + 1] * 256 * 256 + payload[row4B * 4 + 2] * 256 + payload[
                                                            row4B * 4 + 3]) / 8
                                    # print(output_payload_row(payload,row4B))
                                    row4B += 1  # new 32bit row
                                    rr['last_sr_timestamp'] = payload[row4B * 4 + 0] * 256 * 256 * 256 + payload[
                                        row4B * 4 + 1] * 256 * 256 + payload[row4B * 4 + 2] * 256 + payload[row4B * 4 + 3]
                                    # print(output_payload_row(payload,row4B))
                                    row4B += 1  # new 32bit row
                                    rr['delay_since_last_sr_timestamp'] = float('%.2f' % ((payload[
                                                                                               row4B * 4 + 0] * 256 * 256 * 256 +
                                                                                           payload[
                                                                                               row4B * 4 + 1] * 256 * 256 +
                                                                                           payload[row4B * 4 + 2] * 256 +
                                                                                           payload[
                                                                                               row4B * 4 + 3]) / 65536 * 1000))
                                    # print(output_payload_row(payload,row4B))
                                    row4B += 1  # new 32bit row
                                    result['rtcp_compound'][-1]['RTCP_reception_report_list'].append(rr)
                            except Exception as e:
                                print('\nworking on', result['rtcp_compound'][-1]['RTCP_payload_type'])
                                print(self.output_payload_all(payload))
                                print('---- end of payload -----\n\n')
                                print(row4B)
                                # print(output_payload_row(payload,row4B))
                                print(result['rtcp_compound'][-1]['RTCP_SSRC_trunk_list'])
                                print(traceback.format_exc())

                                exit(0)
                        # print(result)
                        if self.test_object == 'webex':
                            if result['rtcp_compound'][-1]['RTCP_payload_type'] == 'SDES':
                                try:
                                    result['rtcp_compound'][-1]['RTP_SRC_trunk_count'] = payload[row4B * 4 + 0] - 128
                                    result['rtcp_compound'][-1]['SDES_report_length'] = payload[row4B * 4 + 2] * 256 + \
                                                                                        payload[row4B * 4 + 3]
                                    # print(output_payload_row(payload,row4B))
                                    row4B += 1  # new 32bit row

                                    result['rtcp_compound'][-1]['RTCP_SSRC_trunk_list'] = []
                                    for i in range(result['rtcp_compound'][-1]['RTP_SRC_trunk_count']):
                                        # each trunk report starts with 32bit boundary, there is no trunk length because the length varies, but there is trunk count.
                                        trunk = {}
                                        trunk['SSRC'] = payload[row4B * 4 + 0] * 256 * 256 * 256 + payload[
                                            row4B * 4 + 1] * 256 * 256 + payload[row4B * 4 + 2] * 256 + payload[
                                                            row4B * 4 + 3]
                                        # print(output_payload_row(payload,row4B))
                                        row4B += 1  # new 32bit row

                                        # each trunk report item list starts with 32bit boundary, there is no item count because it varies, but each item has a length(+2bytes)
                                        # the last item in each trunk has a 32bit boundary, we know the trunk ends when we see END(0)
                                        idx_B = row4B * 4

                                        # print(trunk)
                                        trunk['chunk_item_list'] = []

                                        idx_row = 0
                                        item_count = 0
                                        item_new = True

                                        while payload[idx_B]:
                                            if item_new:
                                                item = {}
                                                item_count += 1
                                                item['text'] = []

                                                item['item_type'] = chunk_item_type_list[payload[row4B * 4 + 0]]

                                                idx_B += 1
                                                idx_row += 1
                                                item['item_length'] = payload[row4B * 4 + 1]
                                                idx_B += 1
                                                idx_row += 1

                                            if item['item_type'] == 'CNAME' or item['item_type'] == 'EMAIL' or item[
                                                'item_type'] == 'PHONE' or item['item_type'] == 'LOC' or item[
                                                'item_type'] == 'TOOL' or item['item_type'] == 'NOTE':
                                                for j in range(item['item_length']):

                                                    item['text'].append(payload[idx_B])
                                                    idx_B += 1
                                                    if idx_row == 3:
                                                        idx_row = 0

                                                        # print(output_payload_row(payload,row4B))
                                                        row4B += 1  # new 32bit row
                                                    else:
                                                        idx_row += 1

                                            elif item['item_type'] == 'PRIV':
                                                item['prefix_length'] = item['item_length'] = payload[row4B * 4 + 2]
                                                idx_B += 1
                                                if idx_row == 4:
                                                    idx_row = 0
                                                    # print(output_payload_row(payload,row4B))
                                                    row4B += 1  # new 32bit row
                                                else:
                                                    idx_row += 1

                                                item['prefix_string'] = []
                                                for j in range(item['prefix_length']):

                                                    item['prefix_string'].append(payload[idx_B])
                                                    idx_B += 1
                                                    if idx_row == 4:
                                                        idx_row = 0
                                                        # print(output_payload_row(payload,row4B))
                                                        row4B += 1  # new 32bit row
                                                    else:
                                                        idx_row += 1

                                                item['text'] = []
                                                for j in range(item['item_length'] - item['prefix_length']):
                                                    item['text'].append(payload[idx_B])
                                                    idx_B += 1
                                                    if idx_row == 4:
                                                        idx_row = 0
                                                        # print(output_payload_row(payload,row4B))
                                                        row4B += 1  # new 32bit row
                                                    else:
                                                        idx_row += 1

                                            trunk['chunk_item_list'].append(item)  # an item ends

                                            if payload[idx_B]:

                                                item_new = False
                                            else:

                                                item_new = True
                                        result['rtcp_compound'][-1]['RTCP_SSRC_trunk_list'].append(trunk)  # a trunk ends
                                        # print(output_payload_row(payload,row4B))
                                        row4B += 1  # new 32bit row

                                except:
                                    print('\nworking on', result['rtcp_compound'][-1]['RTCP_payload_type'])
                                    print(self.output_payload_all(payload))
                                    print('---- end of payload -----\n\n')
                                    print(self.output_payload_row(payload, row4B))

                                    print(traceback.format_exc())
                                    exit(0)
                            elif result['rtcp_compound'][-1]['RTCP_payload_type'] == 'BYE':
                                try:

                                    result['rtcp_compound'][-1]['RTP_SRC_bye_count'] = payload[row4B * 4 + 0] - 128
                                    result['rtcp_compound'][-1]['bye_report_length'] = payload[row4B * 4 + 2] * 256 + \
                                                                                       payload[row4B * 4 + 3]
                                    # print(output_payload_row(payload,row4B))
                                    row4B += 1  # new 32bit row
                                    result['rtcp_compound'][-1]['RTCP_SSRC_bye_list'] = []
                                    for i in range(result['rtcp_compound'][-1]['RTP_SRC_bye_count']):
                                        bye = {}
                                        bye['SSRC'] = payload[row4B * 4 + 0] * 256 * 256 * 256 + payload[
                                            row4B * 4 + 1] * 256 * 256 + payload[row4B * 4 + 2] * 256 + payload[
                                                          row4B * 4 + 3]
                                        # print(output_payload_row(payload,row4B))
                                        row4B += 1  # new 32bit row
                                        idx_row = 0
                                        bye['len'] = payload[row4B * 4 + 0]
                                        bye['text'] = []
                                        idx_B = row4B * 4 + 1
                                        for j in range(bye['len']):
                                            bye['text'].append(payload[idx_B])
                                            idx_B += 1
                                            if idx_row == 4:
                                                idx_row = 0
                                                # print(output_payload_row(payload,row4B))
                                                row4B += 1  # new 32bit row
                                            else:
                                                idx_row += 1
                                        result['rtcp_compound'][-1]['RTCP_SSRC_bye_list'].append(bye)
                                        # print(output_payload_row(payload,row4B))
                                        row4B += 1  # new 32bit row
                                except:
                                    print('\nworking on', result['rtcp_compound'][-1]['RTCP_payload_type'])
                                    print(self.output_payload_all(payload))
                                    print('---- end of payload -----\n\n')
                                    print(self.output_payload_row(payload, row4B))
                                    print(traceback.format_exc())
                                    exit(0)
                            elif result['rtcp_compound'][-1]['RTCP_payload_type'] == 'APP' or result['rtcp_compound'][-1][
                                'RTCP_payload_type'] == 'Payload-specific Feedback':
                                try:
                                    result['rtcp_compound'][-1]['app_sub_type'] = payload[row4B * 4 + 0] - 128
                                    result['rtcp_compound'][-1]['app_report_length'] = payload[row4B * 4 + 2] * 256 + \
                                                                                       payload[row4B * 4 + 3]
                                    # print(output_payload_row(payload,row4B))
                                    row4B += 1  # new 32bit row
                                    result['rtcp_compound'][-1]['app_report_SSRC'] = payload[
                                                                                         row4B * 4 + 0] * 256 * 256 * 256 + \
                                                                                     payload[row4B * 4 + 1] * 256 * 256 + \
                                                                                     payload[row4B * 4 + 2] * 256 + payload[
                                                                                         row4B * 4 + 3]
                                    # print(output_payload_row(payload,row4B))
                                    row4B += 1  # new 32bit row
                                    result['rtcp_compound'][-1]['app_name'] = payload[row4B * 4 + 0] * 256 * 256 * 256 + \
                                                                              payload[row4B * 4 + 1] * 256 * 256 + payload[
                                                                                  row4B * 4 + 2] * 256 + payload[
                                                                                  row4B * 4 + 3]
                                    # print(output_payload_row(payload,row4B))
                                    row4B += 1  # new 32bit row
                                    idx_B = 0
                                    idx_row = 0
                                    result['rtcp_compound'][-1]['app_data'] = []
                                    while result['udp_data_len'] - 32 * 3 - idx_B > 0:

                                        result['rtcp_compound'][-1]['app_data'].append(payload[idx_B])

                                        idx_B += 1
                                        if idx_row == 4:
                                            idx_row = 0
                                            # print(output_payload_row(payload,row4B))
                                            row4B += 1  # new 32bit row
                                        else:
                                            idx_row += 1
                                except:
                                    print('\nworking on', result['rtcp_compound'][-1]['RTCP_payload_type'])
                                    print(self.output_payload_all(payload))
                                    print('---- end of payload -----\n\n')
                                    print(row4B, result['rtcp_compound'][-1]['app_report_length'],
                                          result['rtcp_compound'][-1]['app_report_SSRC'],
                                          result['rtcp_compound'][-1]['app_name'], idx_B)
                                    print(self.output_payload_row(payload, row4B))
                                    print(traceback.format_exc())
                                    exit(0)
                        elif self.test_object == 'jabber':
                            break
                    if result['rtcp_compound'][0]['RTCP_payload_type'] != 'non_rtcp' and result['rtcp_compound'][0][
                        'RTCP_payload_type'] != 'Payload-specific Feedback':
                        # print('\n',result,'\n')
                        # print('\n\nrtcp/udp = %.2f'%packet_percentage)
                        # if result['src_ip'].startswith('9.'):
                        #     direction = 'receive'
                        # else:
                        #     direction = 'send'
                        # print('content_type: %s, %s, %s' % (payload[1] ,result['content_type'], direction))
                        # print('%s\tlength=%s\tTOS=%s\t%s:%s --> %s:%s\t'%(str(datetime.datetime.now()),str(result['udp_data_len']),str(result['TOS']),str(result['src_ip']),str(result['src_port']),str(result['dst_ip']),str(result['dst_port'])))
                        # for report in result['rtcp_compound']:
                        #
                        #     print('\tresult_type=%s'%(str(report['RTCP_payload_type'])),end='\t')
                        #     if report['RTCP_payload_type']=='SR' or report['RTCP_payload_type']=='RR':
                        #         # print(rtp_type)
                        #         print(' | sender_SSRC(self)=%s'%(str(report['RTCP_sender_SSRC'])),end=' | ')
                        #         if report['RTCP_payload_type']=='SR':
                        #             print(' | sender_pkt_count=%s | rtp_timestamp=%s'%(str(report['RTCP_sender_packet_count']),str(report['RTCP_timestamp_rtp'])),end=' | ')
                        #         print(' : ')
                        #
                        #         for rr in report['RTCP_reception_report_list']:
                        #             print('\t\tSSRC=%s | f_lost=%s | c_lost=%s | h_seq=%s | jitter=%s | delay=%s | last_sr_time=%s'%(str(rr['SSRC']),str(rr['fraction_lost']),str(rr['cumulative_lost']),str(rr['highest_sequence']),str(rr['jitter']),str(rr['delay_since_last_sr_timestamp']),str(rr['last_sr_timestamp'])))
                        #
                        #     elif report['RTCP_payload_type']=='SDES':
                        #         print('count=%s'%(str(report['RTP_SRC_trunk_count'])))
                        #         for trunk in report['RTCP_SSRC_trunk_list']:
                        #             print('\t\tSSRC=%s'%(trunk['SSRC']))
                        #             text=''
                        #             for t in item['text']:
                        #                 text+=chr(t)
                        #             for item in trunk['chunk_item_list']:
                        #                 print('\t\t\t%s=%s'%(item['item_type'],text))
                        #
                        #     elif report['RTCP_payload_type']=='BYE':
                        #         print('count=%s'%(str(report['RTP_SRC_bye_count'])))
                        #         for bye in report['RTCP_SSRC_bye_list']:
                        #             print('\tSSRC=%s\ttext=%s'%(bye['SSRC'],bye['text']))
                        #
                        #     elif report['RTCP_payload_type']=='APP' or report['RTCP_payload_type']=='Payload-specific Feedback':
                        #         print('\t\tSSRC=%s'%report['app_report_SSRC'])
                        #         print('\t\t\tapp_sub_type=%s'%report['app_sub_type'])
                        #         text=''
                        #         for t in report['app_name']:
                        #             text+=chr(t)
                        #         print('\t\t\tapp_name=%s'%text)
                        #         text=''
                        #         for t in report['app_data']:
                        #             text+=chr(t)
                        #         print('\t\t\tapp_datae=%s'%text)

                        # print(result)
                        if self.test_object == 'webex':
                            data_dict = {}
                            data_dict['webex cpu usage'], data_dict['webex mem usage'] = self.get_webex_cpu_usage()
                            data_dict['webex_server_ip'] = list(self.webex_server_location.keys())[0]
                            data_dict['webex_server_location'] = list(self.webex_server_location.values())[0]
                            data_dict['content_type'] = result['content_type']
                            data_dict['dscp code'], data_dict['qos class'] = self.get_dscp_code(result['TOS'])
                            if result['src_ip'].startswith('9.'):
                                data_dict['bandwidth'] = int(
                                    (webex_udp_data_octecs_receive * 8 / 1000) / (time.time() - time1))
                                data_dict['client_ip'] = result['src_ip']
                                direction = 'receive'
                            else:
                                data_dict['bandwidth'] = int(
                                    (webex_udp_data_octecs_send * 8 / 1000) / (time.time() - time1))
                                data_dict['client_ip'] = result['dst_ip']
                                direction = 'send'
                            data_dict['direction'] = direction
                            data_dict['lost'] = result['rtcp_compound'][0]['RTCP_reception_report_list'][0]['fraction_lost']
                            data_dict['jitter'] = result['rtcp_compound'][0]['RTCP_reception_report_list'][0]['jitter']
                            data_dict['delay'] = (result['rtcp_compound'][0]['RTCP_reception_report_list'][0][
                                'delay_since_last_sr_timestamp']) / 10
                            data_dict['timestamp'] = int(time.time() * 1000)
                            json_data = {
                                'webex': data_dict,
                                "room": self.task_id
                            }
                            # print(result)
                            # print(json_data)
                            print(result['src_port'], result['dst_port'])
                            # print(payload[1])
                            # print(rtp_type)
                            print(json_data)
                            requests.post('https://ned100.cn.ibm.com:4433/webex', data=json.dumps(json_data), verify=False)

                            if result['content_type'] in ['audio', 'video']:
                                if direction in ['send', 'receive']:
                                    if result['content_type'] == 'audio' and direction == 'send':
                                        temp_list = rtcp_audio_send
                                    elif result['content_type'] == 'audio' and direction == 'receive':
                                        temp_list = rtcp_audio_receive
                                    elif result['content_type'] == 'video' and direction == 'send':
                                        temp_list = rtcp_video_send
                                    elif result['content_type'] == 'video' and direction == 'receive':
                                        temp_list = rtcp_video_receive
                                    rtcp_audio_send.append([data_dict['lost'], data_dict['jitter'], data_dict['delay'],
                                                            data_dict['webex cpu usage'], data_dict['webex mem usage']])
                                    if len(temp_list) == self.save_interval:
                                        total_lost = 0
                                        total_jitter = 0
                                        total_delay = 0
                                        total_cpu_usage = 0
                                        total_mem_usage = 0
                                        for i in temp_list:
                                            total_lost += i[0]
                                            total_jitter += i[1]
                                            total_delay += i[2]
                                            total_cpu_usage += data_dict['webex cpu usage']
                                            total_mem_usage += data_dict['webex mem usage']
                                        avg_lost = total_lost / self.save_interval
                                        avg_jitter = total_jitter / self.save_interval
                                        avg_delay = total_delay / self.save_interval
                                        avg_cpu_usage = total_cpu_usage / self.save_interval
                                        avg_mem_usage = total_mem_usage / self.save_interval
                                        save_data = {
                                            'unix_time': int(time.time()),
                                            'client_ip': data_dict['client_ip'],
                                            'server_ip': data_dict['webex_server_ip'],
                                            'server_location': data_dict['webex_server_location'],
                                            'cpu_usage': ('%.2f' % avg_cpu_usage),
                                            'mem_usage': ('%.2f' % avg_mem_usage),
                                            'dscp_code': data_dict['dscp code'],
                                            'qos_class': data_dict['qos class'],
                                            'packet_type': result['content_type'],
                                            'direction': direction,
                                            'lossrate': avg_lost,
                                            'fraction_lost': result['rtcp_compound'][0]['RTCP_reception_report_list'][0][
                                                'cumulative_lost'],
                                            'bandwidth': data_dict['bandwidth'],
                                            'jitter': avg_jitter,
                                            'delay': avg_delay
                                        }
                                        # print(save_data)
                                        requests.post('https://ned83.cn.ibm.com/api/v2/current/webex_capture/',
                                                      verify=False, json=save_data)
                        elif self.test_object == 'jabber':
                            data_dict = {}
                            data_dict['dscp code'], data_dict['qos class'] = self.get_dscp_code(result['TOS'])
                            if result['src_ip'] == self.client_ip:
                                data_dict['client_ip'] = result['src_ip']
                                data_dict['server_ip'] = result['dst_ip']
                                direction = 'receive'
                            else:
                                data_dict['server_ip'] = result['src_ip']
                                data_dict['client_ip'] = result['dst_ip']
                                direction = 'send'
                            data_dict['direction'] = direction
                            data_dict['lost'] = result['rtcp_compound'][0]['RTCP_reception_report_list'][0]['fraction_lost']
                            data_dict['jitter'] = result['rtcp_compound'][0]['RTCP_reception_report_list'][0]['jitter']
                            data_dict['delay'] = (result['rtcp_compound'][0]['RTCP_reception_report_list'][0][
                                'delay_since_last_sr_timestamp']) / 10
                            data_dict['timestamp'] = int(time.time() * 1000)
                            json_data = {
                                'webex': data_dict,
                                "room": "jabber"
                            }
                            print(json_data)
                            requests.post('https://ned100.cn.ibm.com:4433/webex', data=json.dumps(json_data), verify=False)


def run(args):
    test_object = args['task_type']
    task_id = args['beacon_id']
    c = capture(test_object, task_id)
    t1 = Thread(target=c.packet_capture)
    t2 = Thread(target=c.analysis_packet)
    t1.start()
    t2.start()
    t2.join()


if __name__ == '__main__':
    args = sys.argv[1]
    args = args.replace("'", '"')
    args = json.loads(args)
    # args = {'task_type': 'webex', 'beacon_id':'111111111'}
    run(args)