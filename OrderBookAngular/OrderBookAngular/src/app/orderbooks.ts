import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class OrderBook {

  Ticker:string;
  BidQty:string;
  BidPrice:string;
  AskQty:string;
  AskPrice:string;  

  constructor(AskQty, AskPrice, BidPrice, BidQty, Ticker ) 
  { 
    this.Ticker = Ticker;
    this.BidQty = BidQty;
    this.BidPrice = BidPrice;
    this.AskQty = AskQty;
    this.AskPrice = AskPrice;
  }
}