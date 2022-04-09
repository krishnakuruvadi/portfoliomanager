function set_user_list(users, sel_user) {
    $('#id_user').empty();
    $('#id_user')
        .append($('<option>', { value : '' })
        .text(''));
    var userdropdown = document.getElementById('id_user');

    console.log(users);
    console.log(sel_user)
    for (x in users) {
        user = users[x]
        // create new option element
        var opt = document.createElement('option');
        // create text node to add to option element (opt)
        opt.appendChild( document.createTextNode(user) );
        // set value property of opt
        opt.value = x;
        if (opt.value == sel_user) {
          opt.selected = true;
        }
        // add opt to end of select box (sel)
        userdropdown.appendChild(opt);
    }
    if (sel_user != '' && sel_user != 'AnonymousUser') {
    } else {
        $('#id_goal').empty();
    }
}

function set_currencies(currencies) {
    $('#id_currencies').empty();
    $('#id_currencies')
        .append($('<option>', { value : '' })
        .text(''));
    var dropdown = document.getElementById('id_currencies');
    for (x in currencies) {
      currency = currencies[x]
      // create new option element
      var opt = document.createElement('option');
      // create text node to add to option element (opt)
      opt.appendChild( document.createTextNode(currency) );
      // set value property of opt
      opt.value = currency;
      // add opt to end of select box (sel)
      dropdown.appendChild(opt);
    }
  }

$("#id_user").change(function () {
    var user = $(this).val();
    console.log(user)
    if (user != '') {
        $.ajax({
            url: '/goal/get-goals/'+user,
            success: function (response) {
                set_goals(response);
            }
        });
    } else {
        $('#id_goal').empty();
    }
});

function set_goals(response, sel_goal) {
    var  new_options = response.goal_list;
    $('#id_goal').empty();
    $('#id_goal')
        .append($('<option>', { value : '' })
        .text(''));
    $.each(new_options, function(key, value) {
        console.log(key,value)
        if(sel_goal == key) {
            $('#id_goal')
                .append($('<option>', { value : key })
                .text(value)
                .attr('selected',true));
        } else {
            $('#id_goal')
                .append($('<option>', { value : key })
                .text(value));
        }
    });
}

function get_forex_rate(from_year, from_month, from_day, from_currency, to_currency) {
    forex_ep = '/common/api/get-forex/'+from_year+'/'+from_month+'/'+from_day+'/'+from_currency+'/'+to_currency;
    console.log('getting forex rate', forex_ep)
    var ret = 1;
    $.ajax({
        method:"GET",
        url:forex_ep,
        async: false,
        success: function(data){
          console.log(data)
          for (val in data) {
            console.log('returning ', data[val]);
            ret = data[val];
          }
        },
        error: function(error_data){
          console.log("error")
          console.log(error_data)
        }
    })
    return ret;
}

function set_comparision_chart(my_vals, comp_vals, chart_labels, my_name, comp_name) {
    var canvas = document.getElementById('compare');
    new Chart(canvas, {
        type: 'line',
        data: {
            //labels: ['1', '2', '3', '4', '5'],
            labels: chart_labels,
            datasets: [{
                label: my_name,
                yAxisID: my_name,
                //data: [100, 96, 84, 76, 69],
                data: my_vals,
                borderColor: "#3e95cd",
                fill: false
            }, {
                label: comp_name,
                yAxisID: comp_name,
                //data: [1, 1, 1, 1, 0],
                data: comp_vals,
                borderColor: "#bfff00",
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio:false,
            title: {
                display: true,
                text: my_name + ' vs ' + comp_name
            },
            scales: {
                yAxes: [{
                    id: my_name,
                    type: 'linear',
                    position: 'left',
                }, {
                    id: comp_name,
                    type: 'linear',
                    position: 'right'
                }]
            }
        }
    });
}