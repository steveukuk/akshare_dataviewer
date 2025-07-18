import akshare as ak
import inspect
import csv
ak.news_cctv
def get_param_names(obj):
    try:
        sig = inspect.signature(obj)
        params = [p.name for p in sig.parameters.values() if p.name != "self"]
        return ";".join(params)
    except Exception:
        return ""

def main():
    methods = []
    for name, obj in inspect.getmembers(ak):
        if inspect.isfunction(obj):
            params = get_param_names(obj)
            doc = obj.__doc__ or ""
            methods.append([name, params, doc.strip().replace("\r\n", "\n").replace("\n", "\\n"), ""])
    with open("method_doc.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["方法", "参数", "解释", "例子"])
        writer.writerows(methods)

if __name__ == "__main__":
    main()