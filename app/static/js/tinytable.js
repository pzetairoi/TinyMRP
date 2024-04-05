function tinytablefunc(inputsearch,jobnumber,ordernumber,fileset) {

// console.log(fileset)

$(document).ready(function () {


  //'{{ searchstring}}'
  //alert(searchstring)

  // DataTable
  var tablet = $(document).ready( function () {
      $('#tinytable').DataTable({
        ajax: { 
            url:'/vault/api/part', 
            dataType: "json",
            data: function ( d ) {
                d.jobnumber = jobnumber;
                d.ordernumber=ordernumber;
            }           
      
            },
      //dom: 'Bfrtip',
      serverSide: true,
      deferRender: true,
      processing: true,
      lengthMenu: [ [10, 25, 50,100,250], [10, 25, 50,100,250] ],
      oSearch: {"sSearch": inputsearch},
      columns: [
              
        
        {data: 'pngpath', orderable: false},
        {data: 'partnumber'},
        {data: 'revision'},
        {data: 'description', "defaultContent": "", class: 'editable text'},
        {data: 'process', "defaultContent": ""},
        {data: 'finish', "defaultContent": ""},
        {data: 'material', "defaultContent": ""},
        {render: function (data, type, row) {    
            return [createButton('edit', row.id),createButton('delete', row.id)];    
        }},
        {data: 'oem'},
        {data: 'oem_partnumber'},
        {data: 'classified'},
        {data: 'qty'},

            ],

    select: {
                style:    'multi',
                // selector: ['td:last-child','td:first-child']
            },

            
     buttons: [                  {
                    text: 'Select all',
                    action: function () {
                        var dataTable = $('#treetable').DataTable()
                        dataTable.rows().select();
                    }
                },
                {
                    text: 'Select none',
                    action: function () {
                        var dataTable = $('#treetable').DataTable()
                        dataTable.rows().deselect();
                    }
                },

            ],

        initComplete: function () {
            // Apply the search

            this.api().columns().every( function () {
                var that = this;

                $( 'input', this.footer() ).on( 'keyup change clear', function () {
                    if ( that.search() !== this.value ) {
                        that
                            .search( this.value )
                            .draw();
                    }
                } );
            } );

            //Col initial visibulity
            var dataTable = $('#tinytable').DataTable()
            dataTable.column( 5 ).visible(false);
            dataTable.column( 6 ).visible(false);
            dataTable.column( 7 ).visible(false);
            dataTable.column( 8 ).visible(false);
            dataTable.column(9 ).visible(false);
            dataTable.column( 10 ).visible(false);
            // dataTable.column(11 ).visible(false);
            




        }
    });


    $('a.toggle-vis').on('click', function (e) {
        e.preventDefault();
        var dataTable = $('#tinytable').DataTable()
 
        // Get the column API object
        var column = dataTable.column($(this).attr('data-column'));
 
        // Toggle the visibility
        column.visible(!column.visible());
    });


  });


          // Setup - add a text input to each footer cell
       $('#tinytable tfoot th').each( function () {
      var title = $(this).text();
      if ( title !== 'Preview' && title !== 'Action' ) {
        $(this).html( '<input type="text" placeholder="Search '+title+'" style="width:100px"/>' );
                  } 
      
  } );
      


function createButton(buttonType, rowID) {    
  var buttonText = buttonType == "edit" ? "Edit" : "Delete";  
  //var onclickAction==  
  return '<button class="' + buttonType + '" type="button" >' + buttonText+'</button>';    
} 

    
function fnCreateTextBox(value, fieldprop) {    
  return '<input data-field="' + fieldprop + '" type="text" value="' + value + '" ></input>';    
} 



function fnUpdateDataTableValue($inputCell, value) {    
  var dataTable = $('#tinytable').DataTable();    
  var rowIndex = dataTable.row($($inputCell).closest('tr')).index();   
  //console.log(value, rowIndex, $inputCell) 
  
  var fieldName = $($inputCell).attr('data-field');

  //console.log(fieldName,value)
  
  dataTable.rows().data()[rowIndex][fieldName] = value; 
}    






function fnCreateTextBox(value, fieldprop) {    
      return '<input data-field="' + fieldprop + '" type="text" value="' + value + '" ></input>';    
  } 
 
  
function fnResetControls() {    
      var openedTextBox = $('#tinytable').find('input');    
      $.each(openedTextBox, function (k, $cell) {    
          $(openedTextBox[k]).closest('td').html($cell.value);    
      })    
  } 


$('#tinytable').on('click', 'tbody td .cancel', function (e) {    
      fnResetControls();    
      $('#tinytable tbody tr td .update').removeClass('update').addClass('edit').html('Edit');    
      $('#tinytable tbody tr td .cancel').removeClass('cancel').addClass('delete').html('Delete');    
  });    

$('#tinytable').on('click', 'tbody td .update', function (e) {    

  var openedTextBox = $('#tinytable').find('input');
  var dataTable = $('#tinytable').DataTable(); 

  var partid;
  var partnumber;
  var description ;
  var revision;
  var process;
  // var process2;
  // var process3;
  var material;
  var finish;
  
  var rowref;
  var colref;

  $.each(openedTextBox, function (k, $cell) { 
      if ($cell.placeholder == '') {
      //console.log($cell.placeholder)
      
      fnUpdateDataTableValue($cell, $cell.value);
      rowref = dataTable.row($($cell).closest('tr')).index();  
      colref= dataTable.column($($cell).closest('td')).index();  
      //console.log("rowindex ",rowref,"colindex ",colref) 
      

      $(openedTextBox[k]).closest('td').html($cell.value);  
     
      
      if (colref == 1) {
          partnumber = $cell.value;
          
      }
       else if (colref == 2) {
          revision = $cell.value;}   
         else if (colref == 3) {
          description = $cell.value;}
          else if (colref == 4) {
          process = $cell.value;} 
          else if (colref == 5) {
          finish = $cell.value;}
          else if (colref == 6) {
          material = $cell.value;}
                  
      //console.log(jobid,jobnumber,description,customer)     
      
      
      }

  })  


  //console.log("updated ", dataTable.rows(rowref).data()[0]);
  partnumber = dataTable.rows(rowref).data()[0]['partnumber'];
  revision = dataTable.rows(rowref).data()[0]['revision'];


  var data_tosend={partnumber:partnumber,description:description,
                    revision:revision, process:process,  finish:finish, material:material}
  //console.log(partid,partnumber,revision,description,revision,process,finish);   
  //console.log(data_tosend);     
  
  //console.log("sent data is before?")

  
  var sel_row = dataTable.row( $(this).parents('tr') );


  $('#tinytable tbody tr td .update').removeClass('update').addClass('edit').html('Edit');    
  $('#tinytable tbody tr td .cancel').removeClass('cancel').addClass('delete').html('Delete');  
  
      //send the data back to database

  //var sel_row = $cell;
  // var data_tosend=sel_row.data();

  $.ajax({
      type: "POST",
      url: 'partapi/update',
      dataType: "json",
      data: data_tosend,
      //data: $(clickedRow),

      success: function(response) {
          console.log(response);
      },
      error: function(error) {
           console.log(error);
      }
  });
  

  dataTable.draw();




  });  


$('#tinytable').on('click', 'tbody td .delete', function (e) {    
      fnResetControls();    


      var tablon = $('#tinytable').DataTable();    
      var clickedRow = $($(this).closest('td')).closest('tr');  
      var sel_row = tablon.row( $(this).parents('tr') );
      var data_tosend=sel_row.data();

      //console.log(data_tosend['partnumber'])

      var test="dklfsdlkfs";
     

      // var retVal = confirm($(data_tosend['partnumber']));
      // if( retVal == true ){
      var retVal = confirm("Confirm to delete: "+ data_tosend['partnumber'] + " revision "+ data_tosend['revision'] );
             if( retVal == true ){

             


      $.ajax({
          type: "POST",
          url: '/vault/partapi/delete',
          dataType: "json",
          data: data_tosend,
          //data: $(clickedRow),

          success: function(response) {
              // console.log($(clickedRow));
              //console.log( $(test));
              console.log(response);
          },
          error: function(error) {
              //console.log( $(test));
              console.log(error);
          }
      });


      //Erase the row
      tablon.row($(clickedRow)).remove().draw();
      
      }
  });  



$('#tinytable').on('click', 'tbody td .edit', function (e) {    
  fnResetControls();    
  var dataTable = $('#tinytable').DataTable();    
  var clickedRow = $($(this).closest('td')).closest('tr');    
  

  $(clickedRow).find('td').each(function () {    
      // do your cool stuff    
      if ($(this).hasClass('editable')) {    
          if ($(this).hasClass('text')) {    
              var html = fnCreateTextBox($(this).html(), 'name');    
              $(this).html($(html))  
              console.log(this.type)      
          }    
      }    
  });     
  
  
  $('#tinytable tbody tr td .update').removeClass('update').addClass('edit').html('Edit');    
  $('#tinytable tbody tr td .cancel').removeClass('cancel').addClass('delete').html('Delete');    
  $(clickedRow).find('td .edit').removeClass('edit').addClass('update').html('Update');    
  $(clickedRow).find('td .delete').removeClass('delete').addClass('cancel').html('Cancel');    
 
});        


$("#all-dt").click(function () { 
    var dataTable = $('#tinytable').DataTable()
    dataTable.rows().select();
});

$("#none-dt").click(function () { 
    var dataTable = $('#tinytable').DataTable()
    dataTable.rows().deselect();
});


// $("#compile-dt").click(function () {
//     var dataTable = $('#tinytable').DataTable()
//     var count =  dataTable.rows( { selected: true } )[0].data;
//     var count =  dataTable.rows( { selected: true } ).count();

//     var rowsel=dataTable.rows( { selected: true } );
//     var counter=0   
//     var alldata=[]

//     var filelist=[]

//         for (let i = 0; i < fileset.length; i++) {
//             // console.log( fileset[i]);
//             var dicto={checkbox:"#"+fileset[i]['filetype']+"_cb"};
//             var filecheck="#"+fileset[i]['filetype']+"_cb"
            
//             var checkcheckbox=document.querySelector(filecheck).checked

//             if( checkcheckbox == true ){
//                 filelist.push(fileset[i]['filetype'])
//                 }

        
//         }
//     console.log(filelist)
//     rowsel.data(1).each( function () {

//         alldata=[]
//         $(this).each( function () {
//             // console.log($(this)[0])
//             alldata.push($(this)[0])   
//         } );

//                     } );



//         //console.log($(alldata));
//         var testdata=JSON.stringify(alldata);
//         var fileout=JSON.stringify(filelist);
//         var jobnumber="jobbb";
//         var ordernumber="orderrrr";

//         $.ajax({
//             type: "POST",
//             url: '/vault/api/listfileset',
//             dataType: "json",
//             // data:{"test":"test"},
//             data: {'alldata':testdata, 'filelist':fileout},
            
            
        
//             success: function(response) {
//                 console.log(response)

//                 if(  response != "" ){
//                 window.location = response;}
//                 else{alert("No parts or files selected to extract")}
                
//             },
//             error: function(error) {
//                 console.log(error)
//             }
//         });


//   });







      });


     
    }