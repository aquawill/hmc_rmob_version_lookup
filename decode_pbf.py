import json
from google.protobuf.json_format import MessageToDict
import product_compatibility_partition_pb2 as partition_pb2

def parse_pbf_to_json(pbf_file):
    # 創建 Protocol Buffer 的對象
    partition_data = partition_pb2.VersionsPartition()

    with open(pbf_file, "rb") as f:
        partition_data.ParseFromString(f.read())

    # **關鍵修正點**: 使用 MessageToDict 轉換 Protobuf 物件
    json_data = MessageToDict(partition_data, preserving_proto_field_name=True)

    return json.dumps(json_data, indent=2)

# 測試解析 .pbf
if __name__ == "__main__":
    pbf_file = "C:/Users/guanlwu/PycharmProjects/here_data_api_client_test/response.pbf"
    try:
        json_result = parse_pbf_to_json(pbf_file)
        print(json_result)
    except Exception as e:
        print(f"錯誤: {e}")
