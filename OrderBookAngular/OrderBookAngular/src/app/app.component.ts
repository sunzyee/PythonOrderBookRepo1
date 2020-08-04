import { Component } from '@angular/core';
import { RestService } from './rest.service';
import { OrderBook } from './orderbooks';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
}) 
export class AppComponent {
  title = 'OrderBookAngular';

  constructor(private rs : RestService){}

  headers = ["Ticker","BidQty", "BidPrice", "AskQty", "AskPrice"]

  orderBook : OrderBook[] = [];

  ngOnInit()
  {
        this.rs.readOrderBook()
        .subscribe
          (
            (response) => 
            {
              this.orderBook = response[0]["data"];
            },
            (error) =>
            {
              console.log("No Data Found" + error);
            }

          )
  }
}
