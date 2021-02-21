    sel_usr = '{{user_id|safe}}'

      function get_goals_and_set_report(goal_data){
        console.log(goal_data)
        var table = document.getElementById("goal-table")
        var i;
        for (i=0;i<goal_data.length;i++) {
          var row = table.insertRow(-1)
          goal_entry = goal_data[i]
          var cell0 = row.insertCell(0)
          cell0.innerHTML = i+1
          var cell1 = row.insertCell(1)
          cell1.innerHTML = goal_entry['name']
          var cell2 = row.insertCell(2)
          cell2.innerHTML = goal_entry['start_date']
          var cell3 = row.insertCell(3)
          cell3.innerHTML = goal_entry['curr_val']
          var cell4 = row.insertCell(4)
          cell4.innerHTML = goal_entry['final_val']
          var cell5 = row.insertCell(5)
          cell5.innerHTML = goal_entry['debt']
          var cell6 = row.insertCell(6)
          cell6.innerHTML = goal_entry['equity']
          var cell7 = row.insertCell(7)
          cell7.innerHTML = goal_entry['achieved']+'<small>('+goal_entry['achieve_per']+'%)</small>'
          var cell8 = row.insertCell(8)
          cell8.innerHTML = goal_entry['remaining']+'<small>('+goal_entry['remaining_per']+'%)</small>'
          var cell9 = row.insertCell(9)
          cell9.innerHTML = goal_entry['user']
          var cell10 = row.insertCell(10)
          cell10.innerHTML = goal_entry['notes']
          var cell11 = row.insertCell(11)
          cell11.innerHTML = goal_entry['target_date']
        }
        if (goal_data.length == 0) {
          document.getElementById("goal").style.display="none"
        }
      }

      function get_fd_and_set_report(fd_data){
        console.log(fd_data)
        var table = document.getElementById("fd-table")
        var i;
        for (i=0;i<fd_data.length;i++) {
          var row = table.insertRow(-1)
          fd_entry = fd_data[i]
          var cell0 = row.insertCell(0)
          cell0.innerHTML = i+1
          var cell1 = row.insertCell(1)
          cell1.innerHTML = fd_entry['number']
          var cell2 = row.insertCell(2)
          cell2.innerHTML = fd_entry['bank_name']
          var cell3 = row.insertCell(3)
          cell3.innerHTML = fd_entry['start_date']
          var cell4 = row.insertCell(4)
          cell4.innerHTML = fd_entry['principal']
          var cell5 = row.insertCell(5)
          cell5.innerHTML = fd_entry['roi']
          var cell6 = row.insertCell(6)
          cell6.innerHTML = fd_entry['final_val']
          var cell7 = row.insertCell(7)
          cell7.innerHTML = fd_entry['user']
          var cell8 = row.insertCell(8)
          cell8.innerHTML = fd_entry['notes']
          var cell9 = row.insertCell(9)
          cell9.innerHTML = fd_entry['mat_date']
        }
        if (fd_data.length == 0) {
          document.getElementById("fd").style.display="none"
        }
      }

      function get_epf_and_set_report (epf_data){
        console.log(epf_data)
        var table = document.getElementById("epf-table")
        var i;
        for (i=0;i<epf_data.length;i++) {
          var row = table.insertRow(-1)
          epf_entry = epf_data[i]
          var cell0 = row.insertCell(0)
          cell0.innerHTML = i+1
          var cell1 = row.insertCell(1)
          cell1.innerHTML = epf_entry['number']
          var cell2 = row.insertCell(2)
          cell2.innerHTML = epf_entry['company']
          var cell3 = row.insertCell(3)
          cell3.innerHTML = epf_entry['start_date']
          var cell4 = row.insertCell(4)
          cell4.innerHTML = epf_entry['employee_contribution']
          var cell5 = row.insertCell(5)
          cell5.innerHTML = epf_entry['employer_contribution']
          var cell6 = row.insertCell(6)
          cell6.innerHTML = epf_entry['interest_contribution']
          var cell7 = row.insertCell(7)
          cell7.innerHTML = epf_entry['total']
          var cell8 = row.insertCell(8)
          cell8.innerHTML = epf_entry['user']
          var cell9 = row.insertCell(9)
          cell9.innerHTML = epf_entry['notes']
        }
        if (epf_data.length == 0) {
          document.getElementById("epf").style.display="none"
        }
      }

      function get_espp_and_set_report(espp_data){
        console.log(espp_data)
        var table = document.getElementById("espp-table")
        var i;
        var espp_entries = espp_data['entry']
        for (i=0;i<espp_entries.length;i++) {
          var row = table.insertRow(-1)
          espp_entry = espp_entries[i]
          var cell0 = row.insertCell(0)
          cell0.innerHTML = i+1
          var cell1 = row.insertCell(1)
          cell1.innerHTML = espp_entry['exchange']
          var cell2 = row.insertCell(2)
          cell2.innerHTML = espp_entry['symbol']
          var cell3 = row.insertCell(3)
          cell3.innerHTML = espp_entry['total_purchase_price']
          var cell4 = row.insertCell(4)
          cell4.innerHTML = espp_entry['shares_purchased']
          var cell5 = row.insertCell(5)
          cell5.innerHTML = espp_entry['latest_value']
          var cell6 = row.insertCell(6)
          cell6.innerHTML = espp_entry['gain']
          var cell7 = row.insertCell(7)
          cell7.innerHTML = espp_entry['user']
          var cell8 = row.insertCell(8)
          cell8.innerHTML = espp_entry['as_on_date']
        }
        if (espp_entries.length == 0) {
          document.getElementById("espp").style.display="none"
        }
      }

      function get_ppf_and_set_report(ppf_data){
        console.log(ppf_data)
        var table = document.getElementById("ppf-table")
        var i;
        for (i=0;i<ppf_data.length;i++) {
          var row = table.insertRow(-1)
          ppf_entry = ppf_data[i]
          var cell0 = row.insertCell(0)
          cell0.innerHTML = i+1
          var cell1 = row.insertCell(1)
          cell1.innerHTML = ppf_entry['number']
          var cell2 = row.insertCell(2)
          cell2.innerHTML = ppf_entry['start_date']
          var cell3 = row.insertCell(3)
          cell3.innerHTML = ppf_entry['principal']
          var cell4 = row.insertCell(4)
          cell4.innerHTML = ppf_entry['interest']
          var cell5 = row.insertCell(5)
          cell5.innerHTML = ppf_entry['total']
          var cell6 = row.insertCell(6)
          cell6.innerHTML = ppf_entry['user']
          var cell7 = row.insertCell(7)
          cell7.innerHTML = ppf_entry['notes']
        }
        if (ppf_data.length == 0) {
          document.getElementById("ppf").style.display="none"
        }
      }

      function get_ssy_and_set_report(ssy_data){
        console.log(ssy_data)
        var table = document.getElementById("ssy-table")
        var i;
        for (i=0;i<ssy_data.length;i++) {
          var row = table.insertRow(-1)
          ssy_entry = ssy_data[i]
          var cell0 = row.insertCell(0)
          cell0.innerHTML = i+1
          var cell1 = row.insertCell(1)
          cell1.innerHTML = ssy_entry['number']
          var cell2 = row.insertCell(2)
          cell2.innerHTML = ssy_entry['start_date']
          var cell3 = row.insertCell(3)
          cell3.innerHTML = ssy_entry['principal']
          var cell4 = row.insertCell(4)
          cell4.innerHTML = ssy_entry['interest']
          var cell5 = row.insertCell(5)
          cell5.innerHTML = ssy_entry['total']
          var cell6 = row.insertCell(6)
          cell6.innerHTML = ssy_entry['user']
          var cell7 = row.insertCell(7)
          cell7.innerHTML = ssy_entry['notes']
        }
        if (ssy_data.length == 0) {
          document.getElementById("ssy").style.display="none"
        }
      }

      function get_rsu_and_set_report(rsu_data){
        console.log(rsu_data)
        var table = document.getElementById("rsu-table")
        var i;
        var rsu_entries = rsu_data['entry']
        for (i=0;i<rsu_entries.length;i++) {
          var row = table.insertRow(-1)
          rsu_entry = rsu_entries[i]
          var cell0 = row.insertCell(0)
          cell0.innerHTML = i+1
          var cell1 = row.insertCell(1)
          cell1.innerHTML = rsu_entry['exchange']
          var cell2 = row.insertCell(2)
          cell2.innerHTML = rsu_entry['symbol']
          var cell3 = row.insertCell(3)
          cell3.innerHTML = rsu_entry['shares_for_sale']
          var cell4 = row.insertCell(4)
          cell4.innerHTML = rsu_entry['latest_value']
          var cell5 = row.insertCell(5)
          cell5.innerHTML = rsu_entry['user']
          var cell6 = row.insertCell(6)
          cell6.innerHTML = rsu_entry['as_on_date']
        }
        if (rsu_entries.length == 0) {
          document.getElementById("rsu").style.display="none"
        }
      }

      function get_mf_and_set_report(mf_data){
        console.log(mf_data)
        var table = document.getElementById("mf-table")
        var i;
        var mf_entries = mf_data['folio']
        for (i=0;i<mf_entries.length;i++) {
          var row = table.insertRow(-1)
          mf_entry = mf_entries[i]
          var cell0 = row.insertCell(0)
          cell0.innerHTML = i+1
          var cell1 = row.insertCell(1)
          cell1.innerHTML = mf_entry['folio']
          var cell2 = row.insertCell(2)
          cell2.innerHTML = mf_entry['fund']
          var cell3 = row.insertCell(3)
          cell3.innerHTML = mf_entry['units']
          var cell4 = row.insertCell(4)
          cell4.innerHTML = mf_entry['buy_price']
          var cell5 = row.insertCell(5)
          cell5.innerHTML = mf_entry['buy_value']
          var cell6 = row.insertCell(6)
          cell6.innerHTML = mf_entry['latest_price']
          var cell7 = row.insertCell(7)
          cell7.innerHTML = mf_entry['latest_value']
          var cell8 = row.insertCell(8)
          cell8.innerHTML = mf_entry['gain']
          var cell9 = row.insertCell(9)
          cell9.innerHTML = mf_entry['user']
          var cell10 = row.insertCell(10)
          cell10.innerHTML = mf_entry['notes']
          var cell11 = row.insertCell(11)
          cell11.innerHTML = mf_entry['as_on_date']
        }
        if (mf_entries.length == 0) {
          document.getElementById("mf").style.display="none"
        }
      }

      function get_shares_and_set_report(share_data){
        console.log(share_data)
        var table = document.getElementById("stock-table")
        var i;
        var share_entries = share_data['shares']
        for (i=0;i<share_entries.length;i++) {
          var row = table.insertRow(-1)
          share_entry = share_entries[i]
          var cell0 = row.insertCell(0)
          cell0.innerHTML = i+1
          var cell1 = row.insertCell(1)
          cell1.innerHTML = share_entry['exchange']
          var cell2 = row.insertCell(2)
          cell2.innerHTML = share_entry['symbol']
          var cell3 = row.insertCell(3)
          cell3.innerHTML = share_entry['quantity']
          var cell4 = row.insertCell(4)
          cell4.innerHTML = share_entry['buy_price']
          var cell5 = row.insertCell(5)
          cell5.innerHTML = share_entry['buy_value']
          var cell6 = row.insertCell(6)
          cell6.innerHTML = share_entry['latest_price']
          var cell7 = row.insertCell(7)
          cell7.innerHTML = share_entry['latest_value']
          var cell8 = row.insertCell(8)
          cell8.innerHTML = share_entry['gain']
          var cell9 = row.insertCell(9)
          cell9.innerHTML = share_entry['user']
          var cell10 = row.insertCell(10)
          cell10.innerHTML = share_entry['notes']
          var cell11 = row.insertCell(11)
          cell11.innerHTML = share_entry['as_on_date']
        }
        if (share_entries.length == 0) {
          document.getElementById("stock").style.display="none"
        }
      }
