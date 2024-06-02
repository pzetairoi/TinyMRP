function tinytablefunc(inputsearch,jobnumber,ordernumber,fileset) {

console.log(fileset)

$(document).ready(function () {



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
      lengthMenu: [ [11, 25, 50,100,250], [11, 25, 50,100,250] ],
      oSearch: {"sSearch": inputsearch},
      columns: [
              
        
        {data: 'pngpath', orderable: false},
        {data: 'partnumber'},
        {data: 'revision'},
        {data: 'description'},
        {data: 'process'},
        {data: 'finish'},
        {data: 'material'},
        {data: 'approved'},
        {data: 'oem'},
        {data: 'oem_partnumber'},
        {data: 'thickness'},
        {data: 'mass'},

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
            // dataTable.column( 5 ).visible(false);
            // dataTable.column( 6 ).visible(false);
            dataTable.column( 7 ).visible(false);
            dataTable.column( 8 ).visible(false);
            dataTable.column(9 ).visible(false);
            dataTable.column( 10 ).visible(false);
            dataTable.column(11 ).visible(false);
            

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
      

  





      });


     
    }