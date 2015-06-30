//
//  BuyItemView.swift
//  Bakkle
//
//  Created by Carroll, Joseph B on 6/29/15.
//  Copyright (c) 2015 Ishank Tandon. All rights reserved.
//

import UIKit

class RateUserView: UIViewController {
    
    var item: NSDictionary!
    
    @IBOutlet weak var btnBack: UIButton!
    @IBOutlet weak var sellerImage: UIImageView!
    @IBOutlet weak var sellerLabel: UILabel!
    @IBOutlet weak var itemImage: UIImageView!
    @IBOutlet weak var itemLabel: UILabel!
    @IBOutlet weak var itemPrice: UILabel!
    @IBAction func btnBackAction(sender: AnyObject) {
        self.dismissViewControllerAnimated(true, completion: nil)
    }
    @IBAction func btnSubmit(sender: AnyObject) {
        let alert: UIAlertController = UIAlertController(title: "Bought Item", message: "Accept offer flow is complete; however, this is just a mock for now.", preferredStyle: .Alert)
        alert.addAction(UIAlertAction(title: "OK", style: UIAlertActionStyle.Default, handler: nil))
        self.presentViewController(alert, animated: true, completion: nil)
    }
    
    override func viewDidLoad() {
        setupButtons()
        
        let sellersProfile = item.valueForKey("seller") as! NSDictionary
        let facebookID = sellersProfile.valueForKey("facebook_id") as! String
        let sellersName = sellersProfile.valueForKey("display_name") as! String
        var facebookProfileImgString = "http://graph.facebook.com/\(facebookID)/picture?width=142&height=142"
        
        //TODO: handle case where sellers name is null
        let dividedName = split(sellersName) {$0 == " "}
        let firstName = dividedName[0] as String
        sellerLabel.text = firstName // + " " + lastName + "."
        let profileImgURL = NSURL(string: facebookProfileImgString)
        let sellerFacebookImage = UIImage(data: NSData(contentsOfURL: profileImgURL!)!)
        sellerImage.image = sellerFacebookImage
        
        
        let imgURLs = item.valueForKey("image_urls") as! NSArray
        let topTitle: String = item!.valueForKey("title") as! String
        let topPrice: String = item!.valueForKey("price") as! String
        
        itemLabel.text = topTitle.uppercaseString
        itemPrice.text = "$" + topPrice
        
        let firstURL = imgURLs[0] as! String
        let imgURL = NSURL(string: firstURL)
        if let imgData = NSData(contentsOfURL: imgURL!) {
            dispatch_async(dispatch_get_main_queue()) {
                let itemImage = UIImage(data: imgData)
                self.itemImage.image = itemImage
            }
        }
        sellerImage.clipsToBounds = true
        itemImage.clipsToBounds = true
        sellerImage.layer.cornerRadius = self.itemImage.frame.size.width/2
        itemImage.layer.cornerRadius = self.itemImage.frame.size.width/2
    }
    
    override func viewDidAppear(animated: Bool) {
        sellerImage.layer.cornerRadius = self.itemImage.frame.size.width/2
        itemImage.layer.cornerRadius = self.itemImage.frame.size.width/2
    }
    
    func setupButtons() {
        btnBack.setImage(IconImage().close(), forState: .Normal)
        btnBack.setTitle("", forState: .Normal)
    }
}