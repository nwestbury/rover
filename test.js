const puppeteer = require('puppeteer');
const fs = require('fs');

const CONFIG = require('./config.json');

const login_reddit = async (page) => {
    let cookies;
    if (fs.existsSync(CONFIG.COOKIE_PATH)) {
        const json = JSON.parse(fs.readFileSync(CONFIG.COOKIE_PATH, 'utf8'));
        cookies = json.cookies;
    } else {
        await page.goto('https://www.reddit.com/login/', {timeout: 60000, waitUntil: 'domcontentloaded'});
        await page.waitForSelector('#loginUsername');
        await page.type('#loginUsername', CONFIG.username);
        await page.type('#loginPassword', CONFIG.password);

        await page.click('[type="submit"]');
        await page.waitForNavigation({timeout: 60000, waitUntil: 'networkidle0'});

        cookies = await page.cookies();
        const json = JSON.stringify({cookies});
        fs.writeFileSync(CONFIG.COOKIE_PATH, json, 'utf8');
    }

    return cookies;
}


(async () => {
    const browser = await puppeteer.launch({headless: false});

    const context = browser.defaultBrowserContext();
    await context.overridePermissions('https://www.reddit.com', ['notifications']);

    const page = (await browser.pages())[0];
    page.setDefaultTimeout(60000);


    const cookies = await login_reddit(page);
    console.log('test', cookies);
    await page.setCookie(...cookies);

    const subreddit = 'uwaterloo';
    const topDivs = `div.SubredditVars-r-${subreddit}`;
    await page.goto('https://www.reddit.com/r/uwaterloo/comments/9uhk57/admissions_megathread_fall_2019_incoming_students/?sort=top',
                    {waitUntil: 'domcontentloaded'});
    await page.waitForSelector(`${topDivs}:nth-of-type(2) div`);

    if (await page.$('[data-click-id="upvote"][aria-pressed="false"][id^="upvote-button-"]') !== null) {
        await page.click('[data-click-id="upvote"][aria-pressed="false"][id^="upvote-button-"]');
    }

    await page.evaluate((topDivs) => {
        // Remove margin
        let dom = document.querySelector(`${topDivs}:nth-of-type(2) div`);
        dom.style['margin-top'] = '0px';

        let nodes = document.querySelectorAll('div[data-test-id="post-content"] > div');
        nodes[4].style['display'] = 'none';
        nodes[5].style['display'] = 'none';

        // Delete top of title
        dom = document.querySelector(`${topDivs}:nth-of-type(2) div div div div:nth-of-type(2) div`);
        dom.parentNode.removeChild(dom);

        // Delete header
        dom = document.querySelector(topDivs);
        dom.parentNode.removeChild(dom);
    }, topDivs);

    await page.waitFor(500); // Timeout hack to get shit to work (why do I need this?)

    const selector = `${topDivs}:nth-of-type(1) > div > div > div > div:nth-of-type(2) > div:nth-of-type(2) > div > div > div`;
    console.log('test', selector);
    const largeDiv = await page.$$(selector);
    console.log('se', largeDiv.length);
    await largeDiv[0].screenshot({path: 'title.png'});
    await largeDiv[3].screenshot({path: 'example1.png'});

    await page.evaluate((topDivs) => {
        let nodes = document.querySelectorAll('div[data-test-id="post-content"] > div');
        nodes[4].style['display'] = 'block';
        nodes[5].style['display'] = 'block';
    }, topDivs);

    await largeDiv[0].screenshot({path: 'test1.png'});



    /*
    const text = await page.evaluate(async (selector) => {
        let dom = document.querySelector(selector);
        console.log('got dom', dom.children);
        const title = dom.children[0];
        const comments = dom.children[3];
        
        await title.screenshot({path: 'example.png'});
        return dom.innerHTML;
    }, queryContent);
   
    console.log(':)', text);
    */

    // const html = await page.content();
    // console.log('TEST', html);

    // await browser.close();
    // await page.screenshot({path: 'example.png'});

})();