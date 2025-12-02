import traceback
try:
    from unstructured.partition.auto import partition
    print('SUCCESS')
except:
    traceback.print_exc()