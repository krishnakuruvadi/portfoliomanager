def get_email_html(title, columns, data, total):
        ret = f'<h1>{title}</h1>'
        ret += '<table border="1">'
        for col, col_header in columns.items():
            ret += f'<th>{col_header}</th>'
        for e in data:
            ret += '<tr>'
            for col,_ in columns.items():
                ret+='<td>'+str(e[col])+'</td>'
            ret += '</tr>'
        ret += '<tr><td>Total</td>'
        for _ in range(len(columns)-2):
            ret += '<td></td>'
        ret += '<td>'+str(total)+'</td><tr>'
        ret += '</table>'
        print(f'returning {ret}')
        return ret

def get_weekly_update_table(table_header, col_names, values):
    from django.template.loader import render_to_string
    context = dict()
    context['table_header'] = table_header
    context['col_names'] = col_names
    context['col_values'] = values

    table = render_to_string('email_templates/weekly_email_table.html', context)
    return table