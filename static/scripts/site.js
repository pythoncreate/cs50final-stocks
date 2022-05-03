$(function() {
	$("#symbol").autocomplete({
		source : function(request, response) {
			$.ajax({
				type: "POST",
				url : "/search",
				dataType : "json",
				cache: false,
				data : {
					q : request.term
				},
				success : function(data) {
					var aData=$.map(data, function(item){
						return{
							label: item.Name + " (" + item.Symbol + ")",
							value: item.Symbol
						}
					});
					response(aData);
				},
				error: function(jqXHR, textStatus, errorThrown) {
					console.log(textStatus + " " + errorThrown);
				}
			});
		},
                minLength : 2,
                select: function(event, ui){
                    let stockvalue = ui.item.value;
                    $.ajax({
                            url: "/quote?symbol=" + stockvalue,
                            method: "GET",
                            cache: false
                        }).done(function(data) {
                    
                            // set up a data context for just what we need.
                            var context = {};
                            context.shortName = data.shortName;
                            context.symbol = data.symbol;
                            context.price = data.ask;
                    
                            if(data.quoteType="MUTUALFUND"){
                                context.price = data.previousClose
                            }
                            console.log('context', context)
                    
                            // call the request to load the chart and pass the data context with it.
                            //loadChart(context, stockvalue);
                            window.location.href = "/quote?symbol=" + stockvalue
    
                    })        
		}})})
