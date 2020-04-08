# def validate_oa_annotation(anno):
#     if anno == {}: return False
#     required_keys = ['full', 'resource']
#     required_resource_keys = ['chars', '@type']
    
#     print('check required keys')
#     for key in required_on_keys:
#         if key not in anno.keys(): return False

#     print('check resource keys')
#     for key in required_resource_keys:
#         if isinstance(anno['resource'], list):
#             if key not in anno['resource'][0].keys(): return False
#         elif isinstance(anno['resource'], dict):    
#             if key not in anno['resource'].keys(): return False

#     print('check on')
#     # If 'on', is a list, set to first value for ease.
#     if isinstance(anno['on'], list):
#         anno['on'] = anno['on'][0]

#     anno_on = anno['on']

#     if 'full' not in anno_on.keys(): return False
#     if 'selector' not in anno_on.keys(): return False
#     if 'item' not in anno_on['selector'].keys(): return False

#     anno_item = anno_on['selector']['item']

#     print('check item')
#     required_item_keys = ['@type', 'value']
#     for item_key in required_resource_keys:
#         if item_key not in anno['item'].keys(): return False

#     print('check svg')
#     if anno_item['@type'] == 'oa:SvgSelector':
#         if 'default' not in anno_on['selector']: return False
#         if 'value' not in anno_on['selector']['default']: return False
#         if not anno_on['selector']['default']['value'].startswith('xywh'): return False

#     elif anno_item['@type'] == 'RangeSelector':
#         required_range_sel_keys = ['startSelector', 'endSelector']
        
#         for key in required_range_sel_keys:
#             if key not in anno['item'].keys(): return False
#             if 'value' not in anno['item'][key].keys(): return False
#             if 'refinedBy' not in anno['item'][key].keys(): return False
#             if 'start' not in anno['item']['key']['refinedBy'].keys(): return False
#             if 'end' not in anno['item']['key']['refinedBy'].keys(): return False

        