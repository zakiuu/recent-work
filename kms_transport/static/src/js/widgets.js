function openerp_trip_widget(instance){

    var module = instance.kms_transport;
    var _t     = instance.web._t;

    module.TripOrdersWidget = instance.web.Widget.extend({
        template: 'TripOrdersWidget',
        init: function(parent, params){
            this._super(parent, params);

        },
        load: function(last_order){

        },
        get_order_lines: function(){
               return this.getParent().trip_current_order_lines
        },
        renderElement: function(){
            this._super();
            var self = this;
            var order = this.getParent().get_last_order();
            self.$('.js_trip_prev').click(function(){ self.getParent().previous(); });
            self.$('.js_trip_next').click(function(){ self.getParent().next(); });
            self.$('.js_add_pallets').click(function(){self.getParent().add_pallets($('#pallet_number').val());})
            self.$('#orderName').text(order.sale_id[1]);
            self.$('#orderCustomer').text(order.partner_id[1]);
            self.$('#orderAddress').text(self.getParent().get_current_order_address());
            self.$('#pallet_number').val(self.getParent().get_nb_pallet())
        }
    });

    module.TripPalletWidget = instance.web.Widget.extend({
        template: 'PalletWidget',

        init: function(parent, params){
            this._super(parent, params);
        },
        load: function(last_order){

        },
        renderElement: function(){
            this._super();
            var self = this;
            self.draged_item = null;
            self.$(".js_pallet_sortable").sortable({
                revert: true,
                receive: function(event, ui){
                    self.draged_item = $(ui.item)
                },
                update: function(event, ui ){
                    self.getParent().update_sortable(event, ui, this, self.draged_item)
                }
            });
            self.$(".js_pallet_sortable" ).disableSelection();
            self.$('.js_save_pallet').click(function(){
                self.getParent().save_pallet(this);
            })
            self.$('#weight_ticket').click(function(){self.getParent().weight_ticket($(this).parent().parent().parent().parent().parent().parent())})
            self.$('#pallet_tag').click(function(){self.getParent().print_pallet_tag($(this).parent().parent().parent().parent().parent().parent())})

            self.$("input[name='product_qty']").change(function(){
                var pallet = $(this).parent().parent().parent().parent().parent().parent()
                var pallet_name = pallet.attr('id').split('-')[1]
                var qty = $(this).val()
                var seq = $(this).parent().parent().find('#palletLineSeq').text()
                var i = 0
                var product = null
                var old_qty = 0
                while(i<self.getPallets().length){
                    if (self.getPallets()[i].name == pallet_name){
                        var j = 0
                        while ( j < self.getPallets()[i].items.length){
                            if (self.getPallets()[i].items[j].seq == seq){
                                old_qty = self.getPallets()[i].items[j].quantity
                                self.getPallets()[i].items[j].quantity = parseFloat(qty)
                                product = self.getPallets()[i].items[j].product
                            }
                            j = j + 1
                        }
                    }
                    i = i + 1
                }
                var order_lines = $('.js_drag_order_item')

                i = 0
                while ( i < order_lines.length){

                    if ($($(order_lines[i]).children()[1]).text() == product){
                        var current_remaining_qty = $($(order_lines[i]).children()[5]).text()
                        var remaining_qty = parseFloat(current_remaining_qty) + (parseFloat(old_qty) - parseFloat(qty))
                        $($(order_lines[i]).children()[5]).text(remaining_qty)
                        if (remaining_qty > 0 && ! order_lines[i].draggable){
                            $(order_lines[i]).draggable("enable")
                        }
                        else{
                            if(remaining_qty <= 0){
                                $(order_lines[i]).draggable("disable")
                            }
                        }
                    }
                    i = i + 1
                }
                i =
                self.renderElement()
            })

            self.$('.js_delete_pallet_line').click(function(){
                var seq = $(this).parent().parent().find('#palletLineSeq').text()
                var pallet = $(this).parent().parent().parent().parent().parent().parent()
                var pallet_name = pallet.attr('id').split('-')[1]
                var i = 0
                var product = null
                var qty = 0
                while(i<self.getPallets().length){
                    if (self.getPallets()[i].name == pallet_name){
                        var j = 0
                        while ( j < self.getPallets()[i].items.length){
                            if (self.getPallets()[i].items[j].seq == seq && !self.getPallets()[i].items[j].delete){
                                self.getPallets()[i].items[j].delete = true
                                product = self.getPallets()[i].items[j].product
                                qty = self.getPallets()[i].items[j].quantity
                                break
                            }
                            j = j + 1
                        }
                        j = j + 1
                        var next_seq = null
                        while(j < self.getPallets()[i].items.length){

                            if (! self.getPallets()[i].items[j].delete){
                                next_seq = self.getPallets()[i].items[j].seq
                                self.getPallets()[i].items[j].seq = seq
                                seq = next_seq
                            }else{
                                seq = self.getPallets()[i].items[j].seq
                            }
                            j = j + 1
                        }
                        break
                    }
                    i = i + 1
                }
                var order_lines = $('.js_drag_order_item')

                i = 0
                while ( i < order_lines.length){

                    if ($($(order_lines[i]).children()[1]).text() == product){
                        var current_qty = $($(order_lines[i]).children()[5]).text()

                        $($(order_lines[i]).children()[5]).text(parseInt(current_qty) + parseInt(qty))
                        if (! order_lines[i].draggable){
                            $(order_lines[i]).draggable("enable")
                        }

                    }
                    i = i + 1
                }
                self.renderElement()
            })

            self.$('.js_delete_pallet').click(function(){
                var pallet = $(this).parent().parent().parent()
                var pallet_number = pallet.attr('id').split('-')[1]

                var i = 0
                while(i < self.getPallets().length){
                    if(self.getPallets()[i].name == pallet_number){
                        var j = i + 1
                        self.getPallets()[i].delete = true
                        var next_number = null
                        while ( j < self.getPallets().length){
                            if(! self.getPallets()[j].delete){
                                next_number = self.getPallets()[j].name
                                self.getPallets()[j].new_name = pallet_number
                                pallet_number = next_number
                            }else{
                                pallet_number = self.getPallets()[j].name
                            }
                            j = j +1
                        }
                        break
                    }
                    i = i + 1
                }
                self.renderElement()
            })

            self.$("select[id='new_pallet_position']").change(function(){
                var pallet_number = pallet.attr('id').split('-')[1]
                var i = 0
                while(i < self.getPallets().length){
                    if(self.getPallets()[i].name == pallet_number){
                        self.getPallets()[i].new_name = $(this).val()
                        break
                    }
                    i = i + 1
                }
            })
        },
        getPallets: function(){
            return this.getParent().pallets
        },
        get_pallets_number:function(){
            return this.getParent().pallets_number
        },
        getTrip: function(){
          return this.getParent().trip
        }
    })


    module.TripPalletPadWidget = instance.web.Widget.extend({
        template:'PalletPad',
        init: function(parent, params){
            this._super(parent, params);
        },
        load: function(last_order){

        },
        renderElement: function(){
            this._super();
            var self = this;
            self.$(".js_clicked_pad").click(function(){
                self.getParent().clicked_pad = self.$(this).text()
            })

            self.$('.add_multi_lines').click(function(){
                self.getParent().add_multi_lines()
            })
            self.$('.js_save_pallets').click(function(){
                self.getParent().update_pallets()
            })
        },
        getPallets: function(){
            return this.getParent().pallets
        }

    })

    module.TripWidget = instance.web.Widget.extend({
        template: 'TripWidget',
        init: function(parent,params){
            this._super(parent,params);
            var self = this;

            init_hash = $.bbq.getState();
            this.trip_id = init_hash.trip_id ? init_hash.trip_id:undefined;
            self.trip = null;
            self.trip_current_order = null; // hold the current stock p
            self.trip_current_order_index = 0; // hold the current stock picking index in the trip.stock_picking_ids
            self.trip_current_order_lines = []; // hold the current stock picking items
            self.pallets = null; // holds the pallets for the current order
            self.pallets_number = 0; // holds the number of pallets for the current order
            self.trip_current_order_address = '';
            self.clicked_pad = null;
            this.loaded = this.load(this.trip_id, self.trip_current_order_index);
        },
        load: function(trip_id, current_index){
            var self = this;
            return new instance.web.Model('stock.kms.transport')
                .call('read', [[parseInt(trip_id)], [], new instance.web.CompoundContext()])
                .then(function(trip){
                    self.trip = trip[0];
                }).then(function(){
                    return new instance.web.Model('stock.picking')
                        .call('read', [[parseInt(self.trip.stock_picking_ids[current_index])], [], new instance.web.CompoundContext()])
                        .then(function(picking){
                             self.trip_current_order = picking[0]
                        })
                }).then(function(){
                    return new instance.web.Model('stock.kms.transport')
                        .call('get_order_lines', [[self.trip.id], self.trip.stock_picking_ids[current_index], new instance.web.CompoundContext()])
                        .then(function(move_lines){
                            self.trip_current_order_lines = move_lines
                        })
                }).then(function(){
                    return new instance.web.Model('stock.kms.transport')
                        .call('get_positions', [[self.trip.id], self.trip.stock_picking_ids[current_index],new instance.web.CompoundContext()])
                        .then(function(pallets){
                            self.pallets = pallets
                            self.pallets_number = pallets.length
                        })
                }).then(function(){
                    return new instance.web.Model('stock.kms.transport')
                        .call('get_customer_address',[[self.trip.id], self.trip.stock_picking_ids[current_index] , new instance.web.CompoundContext()])
                        .then(function(address){
                            self.trip_current_order_address = address
                        })
                })
        },
        start: function(){
            this._super();
            var self = this;
            instance.webclient.set_content_full_screen(true);

            this.loaded.then(function(){
                self.trip_orders = new module.TripOrdersWidget(self)
                self.trip_orders.replace(self.$('#tripOrders'))

                self.pallet_pad = new module.TripPalletPadWidget(self)
                self.pallet_pad.replace(self.$('#palletPad'))

                self.trip_pallets = new module.TripPalletWidget(self)
                self.trip_pallets.replace(self.$('#tripPallets'))


                if (self.trip_current_order_index == 0){
                    self.$('.js_trip_prev').addClass('disabled');
                }else{
                    self.$('.js_trip_prev').removeClass('disabled');
                }
                if(self.trip_current_order_index == self.trip.stock_picking_ids.length -1){
                    self.$('.js_trip_next').addClass('disabled');
                }else{
                    self.$('.js_trip_next').removeClass('disabled');
                }

                $( ".js_drag_order_item" ).draggable({
                    connectToSortable: ".js_pallet_sortable",
                    helper: "clone",
                    revert: "invalid"
                });

                var i = 0;
                while (i < $(".js_drag_order_item").length){
                    if(parseFloat($($($(".js_drag_order_item")[i]).children()[5]).text()) <= 0){
                        $($(".js_drag_order_item")[i]).draggable("disable")

                    }
                    i= i + 1
                }

                self.$('.js_trip_quit').click(function(){ self.quit(); });
                self.$('.js_back_to_trip').click(function(){ self.back_to_trip(); });
                self.$('#tripName').text(self.trip.name)
                self.$('#position').text(self.trip.position_ids.length + " Position(s)")
                self.$('#assigned_position').text(self.trip.position_ids.length)
                self.$('#total_position').text(self.trip.total_positions)
                self.$('#orderNb').text(self.trip.stock_picking_ids.length + " Order(s)")
                self.$('#driver').text(self.trip.driver_id[1])
                self.$('#trailer').text(self.trip.trailer_asset_number)
                self.$('#final_dest').text(self.trip.delivery_method[1])
                self.$('#truck').text(self.trip.truck_asset_number)
                self.$('#tripDate').text(self.trip.trip_date)
                self.$('#print_all_in_once_tags').click(function(){self.do_print_all_in_once_tags()})
                self.$('#drop_sheet').click(function(){self.do_print_drop_sheet()})
                self.$('#print_order_tags').click(function(){self.do_print_order_tags()})


            });
        },
        get_last_order: function(){
            return this.trip_current_order
        },
        get_nb_pallet: function(){
            return this.pallets_number
        },
        get_current_order_address: function(){
            return this.trip_current_order_address
        },
//      Next Order
        next: function(){
            var self = this;
            self.trip_current_order_index += 1;
            self.refresh_ui(self.trip_id, self.trip_current_order_index);
            return;
        },
//      Previous Order
        previous: function(){
            var self = this;
            self.trip_current_order_index = self.trip_current_order_index - 1;
            self.refresh_ui(self.trip_id, self.trip_current_order_index);
            return;
        },
        add_multi_lines: function(){
           var self = this;
           var index = null
           if (self.clicked_pad){
               var i = 0
               while(i < self.pallets.length){
                   if (parseInt(self.pallets[i].name) == self.clicked_pad){
                       index = i
                   }
                   i = i  +1
               }
               var seq = self.pallets[index].items.length + 1
               self.$('input:checked').each(function(l){
                   var line = $($('input:checked')[l]).parent().parent()
                   var current_remaining_qty = parseFloat(line.find("#order_line_remaining_qty").text())
                   if (current_remaining_qty > 0){
                       var qty = parseFloat(line.find("#order_line_qty").text())
                       if (qty > 100){
                           qty = 100
                       }
                       self.pallets[index].items.push({
                           seq: parseInt(seq),
                           product: line.find("#order_line_product").text(),
                           quantity: qty,
                           delete: false
                       })
                       seq = seq + 1
                       line.find("#order_line_remaining_qty").text(current_remaining_qty - qty)
                       if (current_remaining_qty - qty <= 0){
                           line.draggable('disable')
                       }
                   }
               })
               self.clicked_pad = null;
               self.$('input:checked').attr('checked',false)
               self.trip_pallets.renderElement()
           }
        },
        add_pallets: function(pallet_number){
           var self = this;
           var diff = pallet_number - self.pallets_number
           if (diff > 0){
               var last_pallet_number = self.trip.position_ids.length + 1
               while (diff > 0){
                   self.pallets.push({
                       items:[],
                       name: last_pallet_number,
                       positions:[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,
                       24, 25, 26, 27, 28, 29, 30],
                       delete: false,
                       picking_id: self.trip_current_order_index,
                       new_name: null
                   })
                   diff = diff - 1
                   last_pallet_number = last_pallet_number + 1
               }
           }
//           self.update_pallets();
           self.pallets_number = self.pallets.length
           self.trip_pallets.renderElement()
//           self.refresh_ui(self.trip_id, self.trip_current_order_index);

        },
        quit: function(){
            this.destroy();
            return new instance.web.Model("ir.model.data").get_func("search_read")([['name', '=', 'action_kms_transport_kanban_view']], ['res_id']).pipe(function(res) {
                    window.location = '/web#action=' + res[0]['res_id'];
                });
        },
        back_to_trip: function(){
            var self = this;
            this.destroy();
            return new instance.web.Model("ir.model.data").get_func("search_read")([['name', '=', 'action_kms_transport_kanban_view']], ['res_id']).pipe(function(res) {
                    window.location = '/web#id=' + self.trip.id + '&view_type=form&model=stock.kms.transport&' + res[0]['res_id'];
            });
        },
        destroy: function(){
            this._super();
            instance.webclient.set_content_full_screen(false);
        },
        save_pallet: function(button){
            var self = this;
            var new_position = null
            var current_position = null
            if (button){
                new_position = $(button).parent().parent().find("#new_pallet_position").val()
                current_position = $(button).parent().parent().find("#pallet_position").text().split(': ')[1]
            }

            var pallet = null
            if(new_position != current_position){
                var i = 0
                while (i < self.pallets.length){
                    if(parseInt(new_position) == parseInt(self.pallets[i].name)){
                        pallet = parseInt(self.pallets[i].name)
                        break
                    }
                    i = i + 1
                }
                if (pallet){
                    var view_dialog = new instance.web.Dialog(self, {
                        title: "Update Position Number",
                        buttons:[
                            {text: 'Update', click: function(){ self.update_pallets(button); view_dialog.close()}},
                            {text: 'Cancel', click: function(){ view_dialog.close()}}
                        ]
                    }, '<p>There is two pallets that have the same number would you like to update any way</p>').open()
                }else{
                    self.update_pallets();
                }
            }else{
                self.update_pallets();
            }

        },
        update_pallets: function(){
            var self = this;
            return new instance.web.Model('stock.kms.transport')
                .call('update_pallets', [[self.trip.id], self.trip.stock_picking_ids[self.trip_current_order_index],self.pallets, new instance.web.CompoundContext()])
                .then(function(){
                    return self.refresh_ui(self.trip.id, self.trip_current_order_index)
                })
        },
        update_sortable: function(event, ui, sortable, dragged_item){
            var self = this;
            var table = $(sortable).parent()
            var pallet_name = $(table).parent().parent().attr('id').split('-')[1]
            // Remove empty row that helped to start the dropping
            var empty_row = table.find("#empty_row")
            if (empty_row != null) {
                empty_row.remove()
            }

            // Retrieve the new product and qty dropped in the pallet
            var product = $(ui.item).find("#order_line_product").text()
            var qty = $(ui.item).find("#order_line_remaining_qty").text()

            if (! product){
                product = $(ui.item).find("#palletLineProduct").text()
            }
            if(! qty){
                qty = $(ui.item).find('input').val()
            }
            // the max qty in a pallet is a 100
            if (parseInt(qty) > 100){
                qty = '100'
            }

            var productHTML = "<td id=\"palletLineProduct\" class=\"pallet-item-desc\">".concat(product, "</td>")
            var qtyHTML = "<td><input  id=\"PalletLineQty\" style=\"width:50px\" type=\"number\" name=\"product_qty\" value=\"".concat(qty,"\"></td>")

            // Style the dragged item to fit the pallet styling and elements
            $(ui.item).html("<td id=\"palletLineSeq\">" + productHTML + qtyHTML +
                "<td><button class=\"btn btn-xs btn-danger js_delete_pallet_line\" style=\"font-size:10px; position: relative; left:-3px\">" +
                    "<span class=\"glyphicon glyphicon-trash\"></span></button></td>")

            // update the table elements sequence using the sorting algorithm
            var pallet_items = table.find('tbody')
            var sequence= 0
            pallet_items.children().each(function(item){
                var line = pallet_items.children()[item]
                if ($(line).find("#palletLineProduct").text() == product){
                    $(line).find("#palletLineSeq").text(item + 1)
                    sequence = item + 1
                }else{
                   if (sequence > 0){
                        sequence = sequence + 1
                        $(line).find("#palletLineSeq").text(sequence)
                   }
                }
            })

            var new_item_list=[]
            pallet_items.children().each(function(item){
                var line = pallet_items.children()[item]
                new_item_list.push({
                    product: $(line).find("#palletLineProduct").text(),
                    seq: $(line).find("#palletLineSeq").text(),
                    quantity:$(line).find("#PalletLineQty").val(),
                    delete: false
                })
            })

            var i = 0
            while (i<self.pallets.length){
                if(self.pallets[i].name == pallet_name){
                    self.pallets[i].items = new_item_list
                    break
                }
                i = i + 1
            }

            var current_remaining_qty = parseInt(dragged_item.find("#order_line_remaining_qty").text())
            dragged_item.find("#order_line_remaining_qty").text(current_remaining_qty - parseInt(qty))
            if (current_remaining_qty - parseInt(qty) <= 0){
                dragged_item.draggable("disable")

            }

            self.trip_pallets.renderElement();
        },
        refresh_ui: function(trip_id, next_index){
            var self = this;
            return this.load(trip_id, next_index).then(function(){
                self.trip_orders.renderElement();
                self.trip_pallets.renderElement();
                self.pallet_pad.renderElement();

                self.$('#position').text(self.trip.position_ids.length + " Position(s)")
                self.$('#assigned_position').text(self.trip.position_ids.length)


                if (self.trip_current_order_index == 0){
                    self.$('.js_trip_prev').addClass('disabled');
                }else{
                    self.$('.js_trip_prev').removeClass('disabled');
                }
                if(self.trip_current_order_index == self.trip.stock_picking_ids.length -1){
                    self.$('.js_trip_next').addClass('disabled');
                }else{
                    self.$('.js_trip_next').removeClass('disabled');
                }

                self.$('.js_add_pallets').click(function(){self.add_pallets($('#pallet_number').val());})

                $( ".js_drag_order_item" ).draggable({
                    connectToSortable: ".js_pallet_sortable",
                    helper: "clone",
                    revert: "invalid"
                });

                var i = 0
                while (i < $(".js_drag_order_item").length){
                    if(parseFloat($($($(".js_drag_order_item")[i]).children()[5]).text()) <= 0){
                        $($(".js_drag_order_item")[i]).draggable("disable")

                    }
                    i= i + 1
                }

            })
        },

        do_print_all_in_once_tags: function(){
            var self = this
            return new instance.web.Model('stock.kms.transport')
                .call('do_print_all_in_once_tags', [[self.trip.id],[], new instance.web.CompoundContext()])
                .then(function(action){
                    return self.do_action(action)
                })
        },

        do_print_order_tags: function(){
            var self = this
            return new instance.web.Model('stock.kms.transport')
                .call('do_print_order_tags', [[self.trip.id],self.trip.stock_picking_ids[self.trip_current_order_index], new instance.web.CompoundContext()])
                .then(function(action){
                    return self.do_action(action)
                })
        },

        do_print_drop_sheet: function(){
            var self = this
            return new instance.web.Model('stock.kms.transport')
                .call('do_print_drop_sheet', [[self.trip.id],[], new instance.web.CompoundContext()])
                .then(function(action){
                    return self.do_action(action)
                })
        },

        weight_ticket: function(pallet){
            var self = this;
            var i = 0
            var pallet_name = pallet.attr('id').split('-')[1]
            while ( i < self.pallets.length){
                if (self.pallets[i].name == pallet_name){
                    console.log("Ticket")
                    if (self.pallets[i].ticket_id){
                        return new instance.web.Model("ir.model.data").get_func("search_read")
                            ([['name', '=', 'action_kms_weighting_trip']], ['res_id']).pipe(function(res) {
                                window.location = '/web#id=' + self.pallets[i].ticket_id + '&view_type=form&model=kms.stock.weighting&' + res[0]['res_id'];
                            });
                    }else{
                        return new instance.web.Model('stock.kms.transport')
                            .call('do_create_weight_ticket', [[self.trip.id], pallet_name, new instance.web.CompoundContext()])
                            .then(function(ticket){
                                return new instance.web.Model("ir.model.data").get_func("search_read")
                                    ([['name', '=', 'action_kms_weighting_trip']], ['res_id']).pipe(function(res) {
                                        window.location = '/web#id=' + ticket + '&view_type=form&model=kms.stock.weighting&' + res[0]['res_id'];
                                    });
                            })
                    }
                }
                i = i + 1
            }
        },

        print_pallet_tag: function(pallet){
            console.log(pallet)
            var self = this
            var pallet_name = parseInt(pallet.attr('id').split('-')[1])
            return new instance.web.Model('stock.kms.transport')
                .call('do_print_pallet_tag', [[self.trip.id], pallet_name, new instance.web.CompoundContext()])
                .then(function(action){
                    return self.do_action(action)
                })
        }
    });
    openerp.web.client_actions.add('transport.ui', 'instance.kms_transport.TripWidget');
}

openerp.kms_transport = function(openerp) {
    openerp.kms_transport = openerp.kms_transport || {};
    openerp_trip_widget(openerp);
}