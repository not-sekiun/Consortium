def main(list_item):
    tmp_dict = {}
    total_imps = []
    for i in list_item:
        filtered_import = i.replace(',', '')
        split_import = filtered_import.split(' ')
        if len(split_import) >= 4:
            if split_import[1] in tmp_dict:
                for i in split_import[3:]:
                    tmp_dict[split_import[1]].append(i)
            else:
                tmp_dict[split_import[1]] = split_import[3:]
        else:
            total_imps.append(i)
    import_statement = ['from ' + i + ' import ' + ', '.join(tmp_dict[i]) for i in tmp_dict]
    return '\n'.join(total_imps + import_statement)
