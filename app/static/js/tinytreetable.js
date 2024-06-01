function tinytreetablefunc(partnumber, revision, jobnumber, ordernumber, fileset, legend) {


    var structure = "tree";
    var consume = "yes";
    var level = "no";


    

    $(document).ready(function() {
        var currentdata;
        var events = $("#events");

        try {
            throw "myException"; // generates an exception
        

        if (consume == "no") {
            document.getElementById("consume").innerHTML = "CONSUMED HIDDEN";
            document.getElementById("consume").style.background = "LightGrey";
        } else {
            document.getElementById("consume").innerHTML = "CONSUMED VISIBLE";
            document.getElementById("consume").style.background = "AliceBlue";
        }

        if (structure == "tree") {
            document.getElementById("structure").innerHTML = "TREE BOM";
            document.getElementById("structure").style.background = "AliceBlue";
        } else {
            document.getElementById("structure").innerHTML = "FLAT BOM";
            document.getElementById("structure").style.background = "LightGrey";
        }

        if (level == "no") {
            document.getElementById("level").innerHTML = "TOP LEVEL ONLY";
            document.getElementById("level").style.background = "AliceBlue";
        } else {
            document.getElementById("level").innerHTML = "FULL BOM";
            document.getElementById("level").style.background = "LightGrey";
        }
        }
            
           catch (e) {
            // statements to handle any exceptions
            console.log(e); // pass exception object to error handler
           }
        // DataTable


        


        var tablet = $(document).ready(function() {

            console.log("INTABLET")


            $("#treetable").DataTable({
                ajax: {
                    url: "/vault/api/treepart",
                    dataType: "json",
                    data: function(d) {
                        d.rootnumber = partnumber;
                        d.rootrevision = revision;
                        d.jobnumber = jobnumber;
                        d.ordernumber = ordernumber;
                        d.structure = structure;
                        d.consume = consume;
                        // d.processlist = JSON.stringify(processlist);
                        d.level = level;
                    },
                },
                dom: "Blfrtip",
                serverSide: true,
                deferRender: true,
                processing: true,
                scrollY: "700px",
                scrollX: true,
                scrollCollapse: true,
                paging: false,

                oLanguage: {
                    sSearch: "Partnumber & description filter:"
                  },

                lengthMenu: [
                    [-1, 10, 25, 50, 100, 250, -1],
                    ["All", 10, 25, 50, 100, 250, "All"],
                ],
                // oSearch: {"sSearch": inputsearch},
                columns: [
                    { data: "level" },
                    { data: "pngpath", orderable: false },
                    { data: "partnumber" },
                    { data: "revision" },
                    { data: "description", defaultContent: "", class: "editable text" },
                    { data: "process", defaultContent: "" },
                    { data: "finish", defaultContent: "" },
                    { data: "material", defaultContent: "" },
                    { data: "qty" },
                    { data: "branchqty" },
                    { data: "totalqty" },
                    // {
                    //     render: function(data, type, row) {
                    //         return [createButton("edit", row.id)];
                    //         // return [createButton('edit', row.id),createButton('delete', row.id)];
                    //     },
                    // },
                    { data: "oem", defaultContent: "", class: "editable text" },
                    { data: "oem_partnumber",  defaultContent: "",  class: "editable text"},
                    { data: "classified", defaultContent: "" },
                    { data: "mass", defaultContent: "" },

                    { data: "category", defaultContent: "" },
                    { data: "colour", defaultContent: "" },

                    // { data: "treatment", defaultContent: "" },
                    // { data: "colour", defaultContent: "" },
                    // { data: "approved", defaultContent: "" },
                    // { data: "author", defaultContent: "" },
                    // { data: "uploader.username", defaultContent: "" },
                    // { data: "spare_Part", defaultContent: "" },
                    // { data: "drawndate", defaultContent: "" },
                ],
                rowCallback: function(row, data, index) {
                    if (jobnumber != "" || ordernumber != "") {
                        if (data.remainingqty > 0) {
                            console.log(
                                "missing",
                                data.partnumber,
                                data.orderedqty,
                                data.totalqty,
                                data.remainingqty
                            );

                            $(row).attr("style", "color:red");
                            $(row).css("text-color", "#99ff9c");
                        }

                        if (data.remainingqty < 0) {
                            $(row).attr("style", "color:purple");
                            console.log(
                                "missing",
                                data.partnumber,
                                data.orderedqty,
                                data.totalqty,
                                data.remainingqty
                            );
                            // $(row).css('background-color','#99ff9c');
                        }

                        if (data.remainingqty == 0) {
                            console.log(
                                "missing",
                                data.partnumber,
                                data.orderedqty,
                                data.totalqty,
                                data.remainingqty
                            );

                            $(row).attr("style", "color:AliceBlue");
                            // $(row).css('background-color','#99ff9c');
                        }
                    }
                },
                columnDefs: [{ width: "10px", targets: [0, 1, 2, 3] }],

                select: {
                    style: "multi",
                    // selector: ['td:last-child','td:first-child']
                },

                buttons: [

                    
                    {
                        text: "Select all",
                        action: function() {
                            var dataTable = $("#treetable").DataTable();
                            dataTable.rows().select();
                        },
                    },
                    {
                        text: "Select none",
                        action: function() {
                            var dataTable = $("#treetable").DataTable();
                            dataTable.rows().deselect();
                        },
                    },



                    // {
                    //     text: "Toggle Top level/full BOM",
                    //     action: function() {
                    //         if (level == "yes") {
                    //             level = "no";
                    //             document.getElementById("level").innerHTML = "TOP LEVEL ONLY";
                    //             document.getElementById("level").style.background = "AliceBlue";
                    //         } else {
                    //             level = "yes";
                    //             document.getElementById("level").innerHTML = "FULL BOM";
                    //             document.getElementById("level").style.background = "LightGrey";
                    //         }

                    //         $("#treetable").DataTable().ajax.reload();
                    //     },
                    // },
                    // {
                    //     text: "Toggle Flat/Treee",
                    //     action: function() {
                    //         if (structure == "tree") {
                    //             structure = "flat";
                    //             $("#treetable").DataTable().column(0).visible(false);
                    //             dataTable.column(8).visible(false);
                    //             dataTable.column(9).visible(false);
                    //             document.getElementById("structure").innerHTML = "FLAT BOM";
                    //             document.getElementById("structure").style.background = "LightGrey";
                    //         } else {
                    //             structure = "tree";
                    //             $("#treetable").DataTable().column(0).visible(true);
                    //             dataTable.column(8).visible(true);
                    //             dataTable.column(9).visible(true);
                    //             document.getElementById("structure").innerHTML = "TREE BOM";
                    //             document.getElementById("structure").style.background = "AliceBlue";
                    //         }

                    //         $("#treetable").DataTable().ajax.reload();
                    //     },
                    // },
                    // {
                    //     text: "Toggle Consumed",
                    //     action: function() {
                    //         console.log(consume);
                    //         if (consume == "no") {
                    //             consume = "yes";
                    //             document.getElementById("consume").innerHTML = "CONSUMED VISIBLE";
                    //             document.getElementById("consume").style.background = "AliceBlue";
                    //         } else {
                    //             consume = "no";
                    //             document.getElementById("consume").innerHTML = "CONSUMED HIDDEN";
                    //             document.getElementById("consume").style.background = "LightGrey";
                    //         }

                    //         $("#treetable").DataTable().ajax.reload();
                    //         console.log(consume);
                    //     },
                    // },






                    // {
                    //     text: "Visual list of selection",
                    //     action: function() {
                    //         var dataTable = $("#treetable").DataTable();
                    //         var rowsel = dataTable.rows({ selected: true });
                    //         var alldata = [];
                
                    //         rowsel.data(1).each(function() {
                    //             alldata = [];
                    //             $(this).each(function() {
                    //                 alldata.push($(this)[0]);
                    //             });
                    //         });
                
                    //         var testdata = JSON.stringify(alldata);
                
                    //         $.ajax({
                    //             type: "POST",
                    //             url: "/vault/api/listvisual",
                    //             dataType: "json",
                    //             data: { alldata: testdata },
                    //             success: function(response) {
                    //                 if (response != "") {
                    //                     window.location = response;
                    //                 } else {
                    //                     alert("No parts selected for visual list");
                    //                 }
                    //             },
                    //             error: function(error) {
                    //                 console.log(error);
                    //             },
                    //         });
                    //     },
                    // },



                    
                    // {
                    //     text: "File extraction of selection and ticked files",
                    //     action: function() {
                    //         var dataTable = $("#treetable").DataTable();
                    //         var rowsel = dataTable.rows({ selected: true });
                    //         var alldata = [];
                    //         var filelist = [];
                
                    //         for (let i = 0; i < fileset.length; i++) {
                    //             console.log( fileset[i]);
                    //             var dicto = { checkbox: "#" + fileset[i]["filetype"] + "_cb" };
                    //             var filecheck = "#" + fileset[i]["filetype"] + "_cb";
                    //             var checkcheckbox = document.querySelector(filecheck).checked;
                    //             if (checkcheckbox == true) {
                    //                 filelist.push(fileset[i]["filetype"]);
                    //             }
                    //         }
                
                    //         rowsel.data(1).each(function() {
                    //             alldata = [];
                    //             $(this).each(function() {
                    //                 alldata.push($(this)[0]);
                    //             });
                    //         });
                
                    //         var testdata = JSON.stringify(alldata);
                    //         var fileout = JSON.stringify(filelist);
                
                    //         $.ajax({
                    //             type: "POST",
                    //             url: "/vault/api/listfileset",
                    //             dataType: "json",
                    //             data: { alldata: testdata, filelist: fileout },
                    //             success: function(response) {
                    //                 if (response != "") {
                    //                     window.location = response;
                    //                 } else {
                    //                     alert("No parts or files selected to extract");
                    //                 }
                    //             },
                    //             error: function(error) {
                    //                 console.log(error);
                    //             },
                    //         });
                    //     },
                    // },







                    

                    {
                        extend: "copyHtml5",
                        // orientation: "landscape",
                        exportOptions: {
                            columns: ":visible",
                        },
                        title: function(  ) {
                            console.log(document.getElementById("parttag").innerHTML); 
                            var exporttitle= document.getElementById("parttag").innerHTML + ":  "
                            exporttitle=exporttitle+  "  Range:" + document.getElementById("level").innerHTML
                            exporttitle=exporttitle+  " - BOM type: " + document.getElementById("structure").innerHTML
                            exporttitle=exporttitle+  "- Subcomponents:" + document.getElementById("consume").innerHTML
                            return exporttitle;
                        
                        },
                    },
                    {
                        extend: "excelHtml5",
                        // orientation: "landscape",
                        exportOptions: {
                            columns: ":visible",
                        },

                        title: function(  ) {
                            
                            var exporttitle= document.getElementById("parttag").innerHTML + ":  "
                            exporttitle=exporttitle+  "  Range:" + document.getElementById("level").innerHTML
                            exporttitle=exporttitle+  " - BOM type: " + document.getElementById("structure").innerHTML
                            exporttitle=exporttitle+  "- Subcomponents:" + document.getElementById("consume").innerHTML
                            return exporttitle;
                        
                        },
                    },
                    {
                        extend: "pdfHtml5",
                        // orientation: "landscape",
                        exportOptions: {
                            columns: ":visible",
                        },
                        
                        title: function(  ) {

                            
                            console.log(document.getElementById("parttag").innerHTML); 
                            var exporttitle= document.getElementById("parttag").innerHTML + ":  "
                            exporttitle=exporttitle+  "  Range:" + document.getElementById("level").innerHTML
                            exporttitle=exporttitle+  " - BOM type: " + document.getElementById("structure").innerHTML
                            exporttitle=exporttitle+  "- Subcomponents:" + document.getElementById("consume").innerHTML
                            return exporttitle;
                        
                        },
                    },
                ],

                initComplete: function() {
                    
                    
 

                    //Col initial visibulity
                    var dataTable = $("#treetable").DataTable();
                    dataTable.column(8).visible(false);
                    dataTable.column(9).visible(false);
                    dataTable.column(10).visible(true);

                    dataTable.column(11).visible(true);
                    dataTable.column(12).visible(false);
                    dataTable.column(13).visible(true);
                    dataTable.column(14).visible(false);
                    dataTable.column(15).visible(false);
                    dataTable.column(16).visible(false);
                    // dataTable.column(17).visible(false);
                    // dataTable.column(18).visible(false);
                    // dataTable.column(19).visible(false);
                    // dataTable.column(20).visible(false);
                    // dataTable.column(21).visible(false);
                    // dataTable.column(22).visible(false);
                    // dataTable.column(23).visible(false);



                   

                    //Dropdown menue
                //     for (let i = 0; i <dataTable.columns().header().length; i++) { 

                //         console.log( dataTable.columns([i])[0][0])
                //         dataTable.columns([i]).every(function () {
                //         var column = this;

                //         var select = $('<select><option value="">partnumber</option></select>')
                //             .appendTo($(column.header()).empty())
                //             .on('change', function () {
                //                 var val = $.fn.dataTable.util.escapeRegex(
                //                     $(this).val()
                //                 );
    
                //                 column
                //                     .search(val ? '^' + val + '$' : '', true, false)
                //                     .draw();
                //             });
    
                //         column.data().unique().sort().each(function (d, j) {
                //             select.append('<option value="' + d + '">' + d + '</option>')
                //         });
                //     });
                // };


                    // Apply the search and the toggle col values
                    this.api()
                    .columns()
                    .every(function() {
                        if (this.visible()){
                            console.log('#toggle-col-'+this[0][0])
                            document.getElementById("toggle-col-"+this[0][0]).style.background = "AliceBlue";
                        }
                        else{
                            document.getElementById("toggle-col-"+this[0][0]).style.background = "LightGrey";
                        }
                         var that = this;
                        $("input", this.header()).on("keyup change clear", function() {
                            if (that.search() !== this.value) {
                                that.search(this.value).draw();
                            }
                        });                     
                    });

                },
            });
            // tablet.searchPanes.container().prependTo(tablet.tablet().container());
            // tablet.searchPanes.resizePanes();
            console.log("INSIDETABLET")

            var dataTable = $("#treetable").DataTable();


            dataTable.on("select", function(e, dt, type, indexes) {
                console.log("click");
                var rowData = dataTable.rows(indexes).data();
                // events.prepend( '<div><b>'+type+' selection</b> - '+JSON.stringify( rowData )+'</div>' );
            });
            dataTable.on("deselect", function(e, dt, type, indexes) {
                console.log("click");
                var rowData = dataTable.rows(indexes).data().toArray();
                // events.prepend( '<div><b>'+type+' <i>de</i>selection</b> - '+JSON.stringify( rowData )+'</div>' );
            });

            $("#treetable tbody").on("click", "td.dt-control", function() {
                var tablet = $("#treetable").DataTable();
                var tr = $(this).closest("tr");
                var row = tablet.row(tr);
                currentdata = console.log("click");
            });

            $("a.toggle-vis").on("click", function(e) {
                e.preventDefault();

                // Get the column API object
                var column = dataTable.column($(this).attr("data-column"));

                // Toggle the visibility
                column.visible(!column.visible())

                $("#treetable").DataTable().columns().every(function() {

                    if (this.visible()){  
                        // console.log("visible",document.getElementById("toggle-col-"+this[0][0]).innerHTML)                      

                        document.getElementById("toggle-col-"+this[0][0]).style.background = "AliceBlue";                   
                    
                    }

                    else{
                        // console.log("NO",document.getElementById("toggle-col-"+this[0][0]).innerHTML)  
                        document.getElementById("toggle-col-"+this[0][0]).style.background = "LightGrey"; 
                    }
                });  

                // console.log("end") ;
            });


            //End of table definition
        });




        // Setup - add a text input to each header cell
        $("#treetable thead tr:eq(0) th").each(function() {
            var title = $(this).text();
            if (
                title !== "Preview" &&
                title !== "Action" &&
                title !== "Level QTY" &&
                title !== "Total level QTY" &&
                title !== "TotalQTY"
            ) {
                $(this).html(
                    title +'<input type="text" placeholder="Filter in ' +
                    title +
                    '" style="width:100px"/>'
                );
            } else {
                $(this).html(title);
            }
        });

        $("#treetable tfoot tr:eq(0) th").each(function() {
            var title = $(this).text();
            console.log($(this).index())

                $(this).html( '<a class="btn btn-xs toggle-vis" onclick="reColCols()" data-column="'
                + $(this).index()
                +'" id="atoggle-col-' +  $(this).index() +'" style="background-color:LightGrey">'+
                "Hide "+ title + "</a>"
                );
                console.log($(this).html())
         
        });




        function createButton(buttonType, rowID) {
            var buttonText = buttonType == "edit" ? "Edit" : "Delete";
            //var onclickAction==
            return (
                '<button class="' +
                buttonType +
                '" type="button" >' +
                buttonText +
                "</button>"
            );
        }

        function fnCreateTextBox(value, fieldprop) {
            return (
                '<input data-field="' +
                fieldprop +
                '" type="text" value="' +
                value +
                '" ></input>'
            );
        }

        function fnUpdateDataTableValue($inputCell, value) {
            var dataTable = $("#treetable").DataTable();
            var rowIndex = dataTable.row($($inputCell).closest("tr")).index();
            console.log(value, rowIndex, $inputCell);

            var fieldName = $($inputCell).attr("data-field");

            console.log(fieldName, value);

            dataTable.rows().data()[rowIndex][fieldName] = value;
        }

        function fnCreateTextBox(value, fieldprop) {
            return (
                '<input data-field="' +
                fieldprop +
                '" type="text" value="' +
                value +
                '" ></input>'
            );
        }

        function fnResetControls() {
            var openedTextBox = $("#treetable").find("input");
            $.each(openedTextBox, function(k, $cell) {
                $(openedTextBox[k]).closest("td").html($cell.value);
            });
        }

        $("#treetable").on("click", "tbody td .cancel", function(e) {
            fnResetControls();
            $("#treetable tbody tr td .update")
                .removeClass("update")
                .addClass("edit")
                .html("Edit");
            $("#treetable tbody tr td .cancel")
                .removeClass("cancel")
                .addClass("delete")
                .html("Delete");
        });

        $("#treetable").on("click", "tbody td .update", function(e) {
            var openedTextBox = $("#treetable").find("input");
            var dataTable = $("#treetable").DataTable();

            var partid;
            var partnumber;
            var description;
            var revision;
            var process;
            var finish;

            var rowref;
            var colref;

            $.each(openedTextBox, function(k, $cell) {
                if ($cell.placeholder == "") {
                    console.log($cell.placeholder);

                    fnUpdateDataTableValue($cell, $cell.value);
                    rowref = dataTable.row($($cell).closest("tr")).index();
                    colref = dataTable.column($($cell).closest("td")).index();
                    //console.log("rowindex ",rowref,"colindex ",colref)

                    $(openedTextBox[k]).closest("td").html($cell.value);

                    if (colref == 2) {
                        partnumber = $cell.value;
                    } else if (colref == 3) {
                        revision = $cell.value;
                    } else if (colref == 4) {
                        description = $cell.value;
                    } else if (colref == 5) {
                        process = $cell.value;
                    } else if (colref == 6) {
                        finish = $cell.value;
                    } else if (colref == 7) {
                        material = $cell.value;
                    }

                    //console.log(jobid,jobnumber,description,customer)
                }
            });

            console.log("updated ", dataTable.rows(rowref).data()[0]);
            partnumber = dataTable.rows(rowref).data()[0]["partnumber"];
            revision = dataTable.rows(rowref).data()[0]["revision"];

            var data_tosend = {
                partnumber: partnumber,
                description: description,
                revision: revision,
                process: process,
                finish: finish,
                oem: oem,
            };
            console.log(
                partid,
                partnumber,
                revision,
                description,
                revision,
                process,
                finish
            );
            console.log(data_tosend);

            console.log("sent data is before?");

            var sel_row = dataTable.row($(this).parents("tr"));

            $("#treetable tbody tr td .update")
                .removeClass("update")
                .addClass("edit")
                .html("Edit");
            $("#treetable tbody tr td .cancel")
                .removeClass("cancel")
                .addClass("delete")
                .html("Delete");

            //send the data back to database

            //var sel_row = $cell;
            // var data_tosend=sel_row.data();

            $.ajax({
                type: "POST",
                url: "/vault/partapi/update",
                dataType: "json",
                data: data_tosend,
                //data: $(clickedRow),

                success: function(response) {
                    console.log(response);
                },
                error: function(error) {
                    console.log(error);
                },
            });

            dataTable.draw();
        });

        $("#treetable").on("click", "tbody td .delete", function(e) {
            fnResetControls();

            var tablon = $("#treetable").DataTable();
            var clickedRow = $($(this).closest("td")).closest("tr");
            var sel_row = tablon.row($(this).parents("tr"));
            var data_tosend = sel_row.data();

            console.log(data_tosend["partnumber"]);
            var retVal = confirm(
                "Confirm to delete: " +
                data_tosend["partnumber"] +
                " revision " +
                data_tosend["revision"]
            );
            if (retVal == true) {
                $.ajax({
                    type: "POST",
                    url: "/vault/partapi/delete",
                    dataType: "json",
                    data: data_tosend,
                    success: function(response) {
                        console.log(response);
                    },
                    error: function(error) {
                        console.log(error);
                    },
                });

                //Erase the row
                tablon.row($(clickedRow)).remove().draw();
            }
        });

        $("#treetable").on("click", "tbody td .edit", function(e) {
            fnResetControls();
            var dataTable = $("#treetable").DataTable();
            var clickedRow = $($(this).closest("td")).closest("tr");

            $(clickedRow)
                .find("td")
                .each(function() {
                    if ($(this).hasClass("editable")) {
                        if ($(this).hasClass("text")) {
                            var html = fnCreateTextBox($(this).html(), "name");
                            $(this).html($(html));
                            console.log(this.type);
                        }
                    }
                });

            $("#treetable tbody tr td .update")
                .removeClass("update")
                .addClass("edit")
                .html("Edit");
            $("#treetable tbody tr td .cancel")
                .removeClass("cancel")
                .addClass("delete")
                .html("Delete");
            $(clickedRow)
                .find("td .edit")
                .removeClass("edit")
                .addClass("update")
                .html("Update");
            $(clickedRow)
                .find("td .delete")
                .removeClass("delete")
                .addClass("cancel")
                .html("Cancel");
        });

        $("#load-dt").click(function() {
            var dataTable = $("#treetable").DataTable();
            var count = dataTable.rows({ selected: true })[0].data;
            var count = dataTable.rows({ selected: true }).count();
            var rowsel = dataTable.rows({ selected: true });
            var counter = 0;
            var alldata = [];
            rowsel.data(1).each(function() {
                alldata = [];
                $(this).each(function() {
                    alldata.push($(this)[0]);
                });
            });


            $.ajax({
                type: "POST",
                url: "/vault/api/listfileset",
                dataType: "json",
                // data:{"test":"test"},
                data: { alldata: JSON.stringify(alldata) },
                success: function(response) {
                    console.log(response);
                    $("#treetable").DataTable().ajax.reload();
                },
                error: function(error) {
                    console.log(error);
                },
            });
        });

        // //Extraction of selected rows for fileset compilation
        // $("#fileset-dt").click(function() {
        //     var dataTable = $("#treetable").DataTable();
        //     var rowsel = dataTable.rows({ selected: true });
        //     var alldata = [];
        //     var filelist = [];

        //     for (let i = 0; i < fileset.length; i++) {
        //         console.log( fileset[i]);
        //         var dicto = { checkbox: "#" + fileset[i]["filetype"] + "_cb" };
        //         var filecheck = "#" + fileset[i]["filetype"] + "_cb";
        //         var checkcheckbox = document.querySelector(filecheck).checked;
        //         if (checkcheckbox == true) {
        //             filelist.push(fileset[i]["filetype"]);
        //         }
        //     }

        //     rowsel.data(1).each(function() {
        //         alldata = [];
        //         $(this).each(function() {
        //             alldata.push($(this)[0]);
        //         });
        //     });

        //     var testdata = JSON.stringify(alldata);
        //     var fileout = JSON.stringify(filelist);

        //     $.ajax({
        //         type: "POST",
        //         url: "/vault/api/listfileset",
        //         dataType: "json",
        //         data: { alldata: testdata, filelist: fileout },
        //         success: function(response) {
        //             if (response != "") {
        //                 window.location = response;
        //             } else {
        //                 alert("No parts or files selected to extract");
        //             }
        //         },
        //         error: function(error) {
        //             console.log(error);
        //         },
        //     });
        // });

        //Extraction of selected rows for fileset compilation
        $("#visual-dt").click(function() {
            var dataTable = $("#treetable").DataTable();
            var rowsel = dataTable.rows({ selected: true });
            var alldata = [];

            rowsel.data(1).each(function() {
                alldata = [];
                $(this).each(function() {
                    alldata.push($(this)[0]);
                });
            });

            var testdata = JSON.stringify(alldata);

            $.ajax({
                type: "POST",
                url: "/vault/api/listvisual",
                dataType: "json",
                data: { alldata: testdata },
                success: function(response) {
                    if (response != "") {
                        window.location = response;
                    } else {
                        alert("No parts selected for visual list");
                    }
                },
                error: function(error) {
                    console.log(error);
                },
            });
        });



        
        $("#level").click(function() {
            if (level == "yes") {
                level = "no";
                document.getElementById("level").innerHTML = "TOP LEVEL ONLY";
                document.getElementById("level").style.background = "AliceBlue";
            } else {
                level = "yes";
                document.getElementById("level").innerHTML = "FULL BOM";
                document.getElementById("level").style.background = "LightGrey";
            }
            $("#treetable").DataTable().ajax.reload();
            
    });      

      
    
        
    $("#structure").click(function() {

        if (structure == "tree") {
            structure = "flat";
            $("#treetable").DataTable().column(0).visible(false);
            $("#treetable").DataTable().column(8).visible(false);
            $("#treetable").DataTable().column(9).visible(false);
            document.getElementById("structure").innerHTML = "FLAT BOM";
            document.getElementById("structure").style.background = "LightGrey";
        } else {
            structure = "tree";
            $("#treetable").DataTable().column(0).visible(true);
            $("#treetable").DataTable().column(8).visible(true);
            $("#treetable").DataTable().column(9).visible(true);
            document.getElementById("structure").innerHTML = "TREE BOM";
            document.getElementById("structure").style.background = "AliceBlue";
        }

        $("#treetable").DataTable().ajax.reload();

});      

      
        
$("#consume").click(function() {
    if (consume == "no") {
        consume = "yes";
        document.getElementById("consume").innerHTML = "CONSUMED VISIBLE";
        document.getElementById("consume").style.background = "AliceBlue";
    } else {
        consume = "no";
        document.getElementById("consume").innerHTML = "CONSUMED HIDDEN";
        document.getElementById("consume").style.background = "LightGrey";
    }

    $("#treetable").DataTable().ajax.reload();

});      




///End of dtatatable def
    });



    /// external functions




    ////end of call fuction     
}