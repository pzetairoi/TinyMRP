
function selectpart(jobnumber) {
    console.log(jobnumber);
    var injobnumber=jobnumber
    

    // Initialize DataTable for #datatable
    $('#datatable').DataTable({
        ajax: { 
            url: '/vault/api/part', 
            dataType: "json",
            data: function (d) {
                d.jobnumber = jobnumber;
                d.onlyjob = "no";
            }
        },
      serverSide: true,
      deferRender: true,
      processing: true,
      lengthMenu: [ [5,10, 25, 50,100,250], [5,10, 25, 50,100,250] ],
      
      columns: [
              
              {data: 'pngpath', orderable: false},
              {data: 'partnumber', class: 'editable text'},
              {data: 'revision'},
              {data: 'description', class: 'editable text'},
              {data: 'process'},
              {data: 'finish', class: 'editable text'},
              {render: function (data, type, row) {    
                    return ['<button class="' + "add" + '" type="button" >' + "Add part"+'</button>'];    
                }},
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
            }
        // Other DataTable options...
    });

    // Initialize DataTable for #jobbomtable
    $('#jobbomtable').DataTable({
        ajax: { 
            url: '/vault/api/part', 
            dataType: "json",
            data: function (d) {
                d.jobnumber = jobnumber;
                d.onlyjob = "yes";
            }
        },
        // Other DataTable options...
        serverSide: true,
            deferRender: true,
            processing: true,
            lengthMenu: [ [5,10, 25, 50,100,250], [5,10, 25, 50,100,250] ],
            
            columns: [
                    
                    {data: 'pngpath', orderable: false},
                    {data: 'partnumber', class: 'editable text'},
                    {data: 'revision'},
                    {data: 'description', class: 'editable text'},
                    {data: 'process'},
                    {data: 'finish', class: 'editable text'},
                    {data: 'qty', class: 'editable text'},
                    {render: function (data, type, row) {    
                          return ['<button class="' + "add" + '" type="button" >' + "Add part"+'</button>',
                          '<button class="' + "remove" + '" type="button" >' + "Remove part"+'</button>'

                    ];    
                      }},
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
              }
    });

    // Setup - add a text input to each footer cell
    $('#datatable').on('click', 'tbody td .add', function (e) {
        var tablon = $('#datatable').DataTable();    
        var sel_row = tablon.row($(this).closest('tr'));
        var data_tosend = sel_row.data();
    
        data_tosend['jobnumber'] = injobnumber;
    
        console.log("sendata" + data_tosend['jobnumber']);
        console.log(data_tosend);
    
        $.ajax({
            type: "POST",
            url: '/vault/jobapi/addtobom',
            dataType: "json",
            data: data_tosend,
            success: function(response) {
                // console.log(response);
                $('#jobbomtable').DataTable().ajax.reload();
                $('#treetable').DataTable().ajax.reload();
            },
            error: function(error) {
                console.log(error);
            }
        });
    });


    $('#jobbomtable').on('click', 'tbody td .add', function (e) {
        var tablon = $('#jobbomtable').DataTable();    
        var sel_row = tablon.row($(this).closest('tr'));
        var data_tosend = sel_row.data();
    
        data_tosend['jobnumber'] = injobnumber;
    
        console.log("sendata" + data_tosend['jobnumber']);
        console.log(data_tosend);
    
        $.ajax({
            type: "POST",
            url: '/vault/jobapi/addtobom',
            dataType: "json",
            data: data_tosend,
            success: function(response) {
                // console.log(response);
                $('#jobbomtable').DataTable().ajax.reload();
                $('#treetable').DataTable().ajax.reload();
            },
            error: function(error) {
                console.log(error);
            }
        });
    });


    $('#jobbomtable').on('click', 'tbody td .remove', function (e) {
   
      
        var tablon = $('#jobbomtable').DataTable();    
        var clickedRow = $($(this).closest('td')).closest('tr');  
        var sel_row = tablon.row( $(this).parents('tr') );
        var data_tosend=sel_row.data();
  
        data_tosend['jobnumber']=injobnumber;
  
        console.log("ssendata"+data_tosend['jobnumber'])
  
        console.log(data_tosend)
  
  
  
        $.ajax({
            type: "POST",
            url: '/vault/jobapi/removefrombom',
            dataType: "json",
            data: data_tosend,
            //data: $(clickedRow),
  
            success: function(response) {
                // console.log($(clickedRow));
                //console.log( $(test));
                
                // console.log(response);
                $('#jobbomtable').DataTable().ajax.reload();
                // $('#treetable').DataTable().ajax.reload();
            },
            error: function(error) {
                //console.log( $(test));
                console.log(error);
            }
        });
  
});


    $('#datatable tfoot th').each( function () {
        var title = $(this).text();
        if ( title !== 'Preview' && title !== 'Action' ) {
        $(this).html( '<input type="text" placeholder="Search '+title+'" style="width:100px"/>' );
                    } 
        
    } );

    $('#jobbomtable tfoot th').each( function () {
        var title = $(this).text();
        if ( title !== 'Preview' && title !== 'Action' ) {
        $(this).html( '<input type="text" placeholder="Search '+title+'" style="width:100px"/>' );
                    } 
        
    } );

// End fo function
}




















































// // Event handler for adding a part
// $('#datatable').on('click', 'tbody td .add', function (e) {
      
//             var tablon = $('#jobbomtable').DataTable();    
//             var clickedRow = $($(this).closest('td')).closest('tr');  
//             var sel_row = tablon.row( $(this).parents('tr') );
//             var data_tosend=sel_row.data();
      
//             data_tosend['jobnumber']=jobnumber;
      
//             console.log("ssendata"+data_tosend['jobnumber'])
      
//             console.log(data_tosend)
      
      
      
//             $.ajax({
//                 type: "POST",
//                 url: '/vault/jobapi/addtobom',
//                 dataType: "json",
//                 data: data_tosend,
//                 //data: $(clickedRow),
      
//                 success: function(response) {
//                     // console.log($(clickedRow));
//                     //console.log( $(test));
                    
//                     console.log(response);
//                     $('#jobbomtable').DataTable().ajax.reload();
//                     $('#treetable').DataTable().ajax.reload();
//                 },
//                 error: function(error) {
//                     //console.log( $(test));
//                     console.log(error);
//                 }
//             });
      
         
            
// });

// Event handler for removing a part

// $(document).ready(function () {
//     selectpart(jobnumber); // Ensure jobnumber is defined
// });











// function selectpart(jobnumber) {

//     console.log(jobnumber);

// $(document).ready(function () {


//   //'{{ searchstring}}'
//   //alert(searchstring)

//   // DataTable
//   var tablet = $(document).ready( function () {
//       $('#datatable').DataTable({
//         // ajax: {
//         //     url: "/vault/api/treepart",
//         //     dataType: "json",
//         //     data: function(d) {
//         //         d.rootnumber = partnumber;
//         //         // d.rootrevision = revision;
//         //         d.jobnumber = "";
//         //         // d.ordernumber = ordernumber;
//         //         // d.structure = structure;
//         //         // d.consume = consume;
//         //         // d.processlist = JSON.stringify(processlist);
//         //         // d.level = level;
//         //     },
//         // },
//       ajax: { 
//         url:'/vault/api/part', 
//         dataType: "json",
//         data: function ( d ) {
//             d.jobnumber = jobnumber;
//             d.onlyjob="no";
//         }           
  
//         },
//       //dom: 'Bfrtip',
//       serverSide: true,
//       deferRender: true,
//       processing: true,
//       lengthMenu: [ [5,10, 25, 50,100,250], [5,10, 25, 50,100,250] ],
      
//       columns: [
              
//               {data: 'pngpath', orderable: false},
//               {data: 'partnumber', class: 'editable text'},
//               {data: 'revision'},
//               {data: 'description', class: 'editable text'},
//               {data: 'process'},
//               {data: 'finish', class: 'editable text'},
//               {render: function (data, type, row) {    
//                     return ['<button class="' + "add" + '" type="button" >' + "Add part"+'</button>'];    
//                 }},
//             ],



//         initComplete: function () {
//             // Apply the search

//             this.api().columns().every( function () {
//                 var that = this;

//                 $( 'input', this.footer() ).on( 'keyup change clear', function () {
//                     if ( that.search() !== this.value ) {
//                         that
//                             .search( this.value )
//                             .draw();
//                     }
//                 } );
//             } );
//         }
//     });
//   });


//           // Setup - add a text input to each footer cell
//        $('#datatable tfoot th').each( function () {
//       var title = $(this).text();
//       if ( title !== 'Preview' && title !== 'Action' ) {
//         $(this).html( '<input type="text" placeholder="Search '+title+'" style="width:100px"/>' );
//                   } 
      
//   } );
      







// $('#datatable').on('click', 'tbody td .add', function (e) {    
      


//       var tablon = $('#datatable').DataTable();    
//       var clickedRow = $($(this).closest('td')).closest('tr');  
//       var sel_row = tablon.row( $(this).parents('tr') );
//       var data_tosend=sel_row.data();

//       data_tosend['jobnumber']=jobnumber;

//       console.log("ssendata"+data_tosend['jobnumber'])

//       console.log(data_tosend)



//       $.ajax({
//           type: "POST",
//           url: '/vault/jobapi/addtobom',
//           dataType: "json",
//           data: data_tosend,
//           //data: $(clickedRow),

//           success: function(response) {
//               // console.log($(clickedRow));
//               //console.log( $(test));
//               console.log(response);
//               $('#jobbomtable').DataTable().ajax.reload();
//               $('#treetable').DataTable().ajax.reload();
//           },
//           error: function(error) {
//               //console.log( $(test));
//               console.log(error);
//           }
//       });


      
      
//   });  




// //       });



//       $(document).ready(function () {


//         //'{{ searchstring}}'
//         //alert(searchstring)
      
//         // DataTable
//         var tablet = $(document).ready( function () {
//             $('#jobbomtable').DataTable({
//             ajax:{ 
//                 url:'/vault/api/part', 
//                 dataType: "json",
//                 data: function ( d ) {
//                     d.jobnumber = jobnumber;
//                     d.onlyjob="yes";
//                 }           
          
//                 },
//             // ajax: {
//             //     url: "/vault/api/treepart",
//             //     dataType: "json",
//             //     data: function(d) {
//             //         // d.rootnumber = partnumber;
//             //         // d.rootrevision = revision;
//             //         d.jobnumber = jobnumber;
//             //         d.onlyjob="yes";
//             //         // d.ordernumber = ordernumber;
//             //         // d.structure = structure;
//             //         // d.consume = consume;
//             //         // d.processlist = JSON.stringify(processlist);
//             //         // d.level = level;
//             //     },
//             },





        //     //dom: 'Bfrtip',
        //     serverSide: true,
        //     deferRender: true,
        //     processing: true,
        //     lengthMenu: [ [5,10, 25, 50,100,250], [5,10, 25, 50,100,250] ],
            
        //     columns: [
                    
        //             {data: 'pngpath', orderable: false},
        //             {data: 'partnumber', class: 'editable text'},
        //             {data: 'revision'},
        //             {data: 'description', class: 'editable text'},
        //             {data: 'process'},
        //             {data: 'finish', class: 'editable text'},
        //             {data: 'qty', class: 'editable text'},
        //             {render: function (data, type, row) {    
        //                   return ['<button class="' + "add" + '" type="button" >' + "Add part"+'</button>',
        //                   '<button class="' + "remove" + '" type="button" >' + "Remove part"+'</button>'

        //             ];    
        //               }},
        //           ],
      
      
      
        //       initComplete: function () {
        //           // Apply the search
      
        //           this.api().columns().every( function () {
        //               var that = this;
      
        //               $( 'input', this.footer() ).on( 'keyup change clear', function () {
        //                   if ( that.search() !== this.value ) {
        //                       that
        //                           .search( this.value )
        //                           .draw();
        //                   }
        //               } );
        //           } );
        //       }
        //   });
        // });
      
      
        //         // Setup - add a text input to each footer cell
        //      $('#jobbomtable tfoot th').each( function () {
        //     var title = $(this).text();
        //     if ( title !== 'Preview' && title !== 'Action' ) {
        //       $(this).html( '<input type="text" placeholder="Search '+title+'" style="width:100px"/>' );
        //                 } 
            
        // } );
            
      
      
      
      
      
      
      
//       $('#jobbomtable').on('click', 'tbody td .add', function (e) {    
            
      
      
//             var tablon = $('#jobbomtable').DataTable();    
//             var clickedRow = $($(this).closest('td')).closest('tr');  
//             var sel_row = tablon.row( $(this).parents('tr') );
//             var data_tosend=sel_row.data();
      
//             data_tosend['jobnumber']=jobnumber;
      
//             console.log("ssendata"+data_tosend['jobnumber'])
      
//             console.log(data_tosend)
      
      
      
//             $.ajax({
//                 type: "POST",
//                 url: '/vault/jobapi/addtobom',
//                 dataType: "json",
//                 data: data_tosend,
//                 //data: $(clickedRow),
      
//                 success: function(response) {
//                     // console.log($(clickedRow));
//                     //console.log( $(test));
                    
//                     console.log(response);
//                     $('#jobbomtable').DataTable().ajax.reload();
//                     $('#treetable').DataTable().ajax.reload();
//                 },
//                 error: function(error) {
//                     //console.log( $(test));
//                     console.log(error);
//                 }
//             });
      
      
            
            
//         });  
      
      
//         $('#jobbomtable').on('click', 'tbody td .remove', function (e) {    
            
      
      
//             var tablon = $('#jobbomtable').DataTable();    
//             var clickedRow = $($(this).closest('td')).closest('tr');  
//             var sel_row = tablon.row( $(this).parents('tr') );
//             var data_tosend=sel_row.data();
      
//             data_tosend['jobnumber']=jobnumber;
      
//             console.log("ssendata"+data_tosend['jobnumber'])
      
//             console.log(data_tosend)
      
      
      
//             $.ajax({
//                 type: "POST",
//                 url: '/vault/jobapi/removefrombom',
//                 dataType: "json",
//                 data: data_tosend,
//                 //data: $(clickedRow),
      
//                 success: function(response) {
//                     // console.log($(clickedRow));
//                     //console.log( $(test));
                    
//                     console.log(response);
//                     $('#jobbomtable').DataTable().ajax.reload();
//                     $('#treetable').DataTable().ajax.reload();
//                 },
//                 error: function(error) {
//                     //console.log( $(test));
//                     console.log(error);
//                 }
//             });
      
      
            
            
//         });
      
//             });
      
      

// //End of top level function selectpart     
//     }