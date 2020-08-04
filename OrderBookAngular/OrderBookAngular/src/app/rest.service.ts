import { Injectable, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { OrderBook } from './orderbooks';
 
@Injectable({
  providedIn: 'root'
})
export class RestService implements OnInit {

  constructor(private http : HttpClient) { }

  ngOnInit() {}
  
  orderBookUrl : string = "http://127.0.0.1:5000/orderbooks";

  readOrderBook()
  {
      return this.http.get<OrderBook[]>(this.orderBookUrl);
  }
}
