//
//  MenuTableView.swift
//  Bakkle
//
//  Created by Sándor A. Pethes on 4/9/15.
//  Copyright (c) 2015 Bakkle Inc. All rights reserved.
//

import UIKit

class MenuTableController: UITableViewController {
    
    var backView: UIView!
    
    @IBOutlet weak var profileImg: UIImageView!
    @IBOutlet weak var nameLabel: UILabel!
    @IBOutlet weak var feedImg: UIImageView!
    @IBOutlet weak var sellerImg: UIImageView!
    @IBOutlet weak var buyerImg: UIImageView!
    @IBOutlet weak var holdImg: UIImageView!
    @IBOutlet weak var contactImg: UIImageView!
    @IBOutlet weak var settingButton: UIButton!
    
    var imgURL: NSURL!
    override func viewDidLoad() {
        super.viewDidLoad()
        
        /* Reveal */
        if self.revealViewController() != nil {
            self.view.addGestureRecognizer(self.revealViewController().panGestureRecognizer())
        }
        var facebookProfileImageUrlString = "http://graph.facebook.com/\(Bakkle.sharedInstance.facebook_id_str)/picture?width=250&height=250"
        imgURL = NSURL(string: facebookProfileImageUrlString)
    
        setupImages()
        setupBackground()
        setupProfileLabel()
        settingButton.setImage(IconImage().settings(), forState: UIControlState.Normal)
    }
    
    override func viewWillAppear(animated: Bool) {
        super.viewWillAppear(animated)
        
        /* set up the function of pushing back frontViewController when tapped frontViewController */
        if self.revealViewController() != nil {
            self.view.addGestureRecognizer(self.revealViewController().panGestureRecognizer())
            
            backView = UIView(frame: self.revealViewController().frontViewController.view.frame)
            //backView.backgroundColor = UIColor(red: CGFloat(1.0), green: CGFloat(0.0), blue: CGFloat(0.0), alpha: CGFloat(1.0))
            self.revealViewController().frontViewController.view.addSubview(backView)
            self.revealViewController().frontViewController.view.addGestureRecognizer(self.revealViewController().tapGestureRecognizer())
        }
    }
    override func viewDidAppear(animated: Bool) {
        setupProfileImg()
    }
    
    override func viewDidDisappear(animated: Bool) {
        super.viewDidDisappear(animated)
        
        if self.revealViewController() != nil {
           backView.removeFromSuperview()
        }
        
    }
    
    override func didReceiveMemoryWarning() {
        super.didReceiveMemoryWarning()
        // Dispose of any resources that can be recreated.
    }
    
    func setupImages() {
        self.feedImg.image = IconImage().home()
        self.sellerImg.image = IconImage().edit()
        self.buyerImg.image = IconImage().cart()
        self.holdImg.image = IconImage().down()
        self.contactImg.image = IconImage().contact()
    }
    
    func setupBackground() {
        var visualEffectView = UIVisualEffectView(effect: UIBlurEffect(style: .Dark)) as UIVisualEffectView
        visualEffectView.frame = tableView.bounds
        var backgroundImageView = UIImageView(frame: tableView.bounds)
        backgroundImageView.hnk_setImageFromURL(imgURL!)
        backgroundImageView.clipsToBounds = true
        backgroundImageView.addSubview(visualEffectView)
        tableView.backgroundView = backgroundImageView
    }
    
    func setupProfileImg() {
        self.profileImg.hnk_setImageFromURL(imgURL!)
        self.profileImg.layer.cornerRadius = self.profileImg.frame.size.width/2
        self.profileImg.layer.borderWidth = 6
        self.profileImg.clipsToBounds = true
        let borderColor = UIColor(red: 0.7, green: 0.7, blue: 0.7, alpha: 1.0)
        self.profileImg.layer.borderColor = borderColor.CGColor
    }
    
    func setupProfileLabel() {
        self.nameLabel.text = Bakkle.sharedInstance.first_name + " " + Bakkle.sharedInstance.last_name
    }
    
    @IBAction func btnContact(sender: AnyObject) {
        UIApplication.sharedApplication().openURL(NSURL(string: "http://www.bakkle.com/")!)
    }
    
    override func tableView(tableView: UITableView, willDisplayCell cell: UITableViewCell, forRowAtIndexPath indexPath: NSIndexPath) {
        /* This fixes the small lines on the left hand side of the cell dividers */
        cell.backgroundColor = UIColor.clearColor()
    }
}



