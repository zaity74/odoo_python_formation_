  if(this.state.context.params.model === 'fa.replenish.product.byvendor'){
                const _state = this.state.data;
                for(var index = 0; index < _state.length; index++){
                    // Return the total value to 0, every time we click on the checkbox
                    _state[index].data.total = 0;
                    /**
                     * If it's equal to 0, check if all the checked checkbox are present in the _state[index].data object
                     * And then sum them all and return them into the total column.
                    **/
                    for(var i=0; i < this.optionalColumnsEnabled.length; i++){
                        var x = this.optionalColumnsEnabled[i];
                        if(x in _state[index].data){
                            _state[index].data.total += _state[index].data[x];
                        };
                    };
                };
        }else{
            console.log("The table doesn't exist");
        }