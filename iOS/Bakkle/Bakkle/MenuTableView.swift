//
//  MenuTableView.swift
//  Bakkle
//
//  Created by Sándor A. Pethes on 4/9/15.
//  Copyright (c) 2015 Bakkle Inc. All rights reserved.
//

import UIKit

class MenuTableController: UITableViewController {

    let profileSegue = "PushToProfileView"
    var backView: UIView!
    var user: NSDictionary!
    
    @IBOutlet weak var profileImg: UIImageView!
    @IBOutlet weak var nameLabel: UILabel!
    @IBOutlet weak var feedImg: UIImageView!
    @IBOutlet weak var sellerImg: UIImageView!
    @IBOutlet weak var buyerImg: UIImageView!
    @IBOutlet weak var holdImg: UIImageView!
    @IBOutlet weak var contactImg: UIImageView!
    @IBOutlet weak var profileBtn: UIImageView!
       
    override func viewDidLoad() {
        super.viewDidLoad()
    
        setupImages()
        profileBtn.image = IconImage().settings()
        self.tableView.tableFooterView = UIView()
    }
    
    override func viewWillAppear(animated: Bool) {
        super.viewWillAppear(animated)
        self.view.userInteractionEnabled = true
        
        /* set up the function of pushing back frontViewController when tapped frontViewController */
        if self.revealViewController() != nil {
            self.view.addGestureRecognizer(self.revealViewController().panGestureRecognizer())
            
            backView = UIView(frame: self.revealViewController().frontViewController.view.frame)
            self.revealViewController().frontViewController.view.addSubview(backView)
            self.revealViewController().frontViewController.view.addGestureRecognizer(self.revealViewController().tapGestureRecognizer())
        }
    }
    override func viewDidAppear(animated: Bool) {
        super.viewDidAppear(animated)
        UIApplication.sharedApplication().statusBarHidden = true
        self.revealViewController().setNeedsStatusBarAppearanceUpdate()
        setupProfileImg()
        setupBackground()
        setupProfileLabel()
    }
    
    override func viewWillDisappear(animated: Bool) {
        super.viewWillDisappear(animated)
        UIApplication.sharedApplication().setStatusBarHidden(false, withAnimation: UIStatusBarAnimation.None)
        self.revealViewController().setNeedsStatusBarAppearanceUpdate()
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
        visualEffectView.frame = tableView.frame
        var backgroundImageView = UIImageView(frame: tableView.frame)
        backgroundImageView.contentMode = UIViewContentMode.ScaleAspectFill
        let finalString = Bakkle.sharedInstance.profileImageURL() + "?width=142&height=142"
        backgroundImageView.hnk_setImageFromURL(NSURL(string: finalString)!)
        backgroundImageView.clipsToBounds = true
        backgroundImageView.addSubview(visualEffectView)
        tableView.backgroundView = backgroundImageView
    }
    
    func setupProfileImg() {
        let finalString = Bakkle.sharedInstance.profileImageURL() + "?width=142&height=142"
        let url = NSURL(string: finalString)
        self.profileImg.hnk_setImageFromURL(url!)
        self.profileImg.layer.cornerRadius = self.profileImg.frame.size.width/2
        self.profileImg.layer.borderWidth = 5.0
        self.profileImg.clipsToBounds = true
        let borderColor = UIColor.whiteColor()
        self.profileImg.layer.borderColor = borderColor.CGColor
    }
    
    func setupProfileLabel() {
        if Bakkle.sharedInstance.account_type == Bakkle.bkAccountTypeGuest || Bakkle.sharedInstance.first_name == nil || Bakkle.sharedInstance.last_name  == nil {
            self.nameLabel.text = "Guest"
        }else{
            self.nameLabel.text = Bakkle.sharedInstance.first_name + " " + Bakkle.sharedInstance.last_name
        }
    }
    
    @IBAction func btnContact(sender: AnyObject) {
        UIApplication.sharedApplication().openURL(NSURL(string: "http://www.bakkle.com/contact/")!)
    }
    
    override func tableView(tableView: UITableView, willDisplayCell cell: UITableViewCell, forRowAtIndexPath indexPath: NSIndexPath) {
        /* This fixes the small lines on the left hand side of the cell dividers */
        cell.backgroundColor = UIColor.clearColor()
        if (indexPath.row == 2 && Bakkle.sharedInstance.flavor == Bakkle.GOODWILL) {
            cell.hidden = true
        }
    }
    
    override func tableView(tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        if Bakkle.developerTools {
            return 5
        }
        return 6
    }
    
    override func tableView(tableView: UITableView, heightForRowAtIndexPath indexPath: NSIndexPath) -> CGFloat {
        if indexPath.row == 0 {
            return 177
        }
        if (indexPath.row == 2 && Bakkle.sharedInstance.flavor == Bakkle.GOODWILL) {
            return 0
        }
        return 60
    }
    
    override func tableView(tableView: UITableView, didSelectRowAtIndexPath indexPath: NSIndexPath) {
        if indexPath.row == 0 {
            if !Bakkle.sharedInstance.isInternetConnected() {
                self.noInternetConnectionAlert()
                return
            }
            self.view.userInteractionEnabled = false
            Bakkle.sharedInstance.getAccount(Bakkle.sharedInstance.account_id, success: { (account: NSDictionary) -> () in
                self.user = account
                dispatch_async(dispatch_get_main_queue(), { () -> Void in
                    self.performSegueWithIdentifier(self.profileSegue, sender: self)
                })
                }, fail: {})
        }
    }
    
    override func prepareForSegue(segue: UIStoryboardSegue, sender: AnyObject?) {
        self.view.userInteractionEnabled = false
        if segue.identifier == self.profileSegue {
            let destinationVC = segue.destinationViewController as! ProfileView
            if self.user != nil {
                destinationVC.user = self.user
            }
        }
    }
    
    func noInternetConnectionAlert(){
        var alert = UIAlertController(title: "No Internet", message: "There was an error! Please check your Network Connection and try again", preferredStyle: UIAlertControllerStyle.Alert)
        alert.addAction(UIAlertAction(title: "OK", style: UIAlertActionStyle.Default, handler: nil))
        self.presentViewController(alert, animated: true, completion: nil)
        
    }
}



