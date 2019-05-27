const puppeteer = require('puppeteer');
const createCsvWriter = require('csv-writer').createObjectCsvWriter;
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

const sentence_regex = /([^,\.!\?;]+[,\.!\?;]+)|([^,\.!\?;]+$)/g;
const split_paragraphs = (paras) => {
    let flattened_sentences = [];
    const para_sentences = paras.map((para) => {
        const split = para.match(sentence_regex);

        let prev = "";
        const sentences = split.map((sentence) => {
            prev += sentence;
            return prev;
        });

        flattened_sentences = flattened_sentences.concat(split);

        return sentences;
    });

    return [flattened_sentences, para_sentences];
}
const addslashes = (str) => (str + '').replace(/[\\"']/g, '\\$&').replace(/\u0000/g, '\\0');

const exposed_funcs = [split_paragraphs];


(async () => {
    const browser = await puppeteer.launch({headless: false});

    const context = browser.defaultBrowserContext();
    await context.overridePermissions('https://www.reddit.com', ['notifications']);

    const page = (await browser.pages())[0];
    page.setDefaultTimeout(60000);
    page.on('console', consoleObj => console.log(consoleObj.text()));

    await page.setViewport({ width: 800, height: 600, deviceScaleFactor: 2 })

    // Functions need to be explicitely expose to be acessed within the node context
    exposed_funcs.forEach(async (func) => {
        await page.exposeFunction(func.name, func);
    });

    const cookies = await login_reddit(page);
    await page.setCookie(...cookies);

    const subreddit = 'uwaterloo';
    const topDivs = `div.SubredditVars-r-${subreddit}`;
    await page.goto('https://www.reddit.com/r/uwaterloo/comments/9uhk57/?sort=top',
                    {waitUntil: 'domcontentloaded'});
    await page.waitForSelector(`${topDivs}:nth-of-type(2) div`);

    // Up vote page :)
    if (await page.$('[data-click-id="upvote"][aria-pressed="false"][id^="upvote-button-"]') !== null) {
        await page.click('[data-click-id="upvote"][aria-pressed="false"][id^="upvote-button-"]');
    }

    // Delete stuff from the page that is unnecessary
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

    // Take screenshot of just the title and upvote buttons
    const selector = `${topDivs}:nth-of-type(1) > div > div > div > div:nth-of-type(2) > div:nth-of-type(2) > div > div > div`;
    const largeDiv = await page.$$(selector);
    const titleDiv = largeDiv[0];
    await titleDiv.screenshot({path: 'img/title.jpeg', quality: 100});

    // Re-display the post-content text and comment numbers
    await page.evaluate(() => {
        let nodes = document.querySelectorAll('div[data-test-id="post-content"] > div');
        nodes[4].style['display'] = 'block';
        // nodes[5].style['display'] = 'block';
    });

    const nodes = await page.$$('div[data-test-id="post-content"] > div');
    const title = await page.evaluate(div => div.textContent.trim(), nodes[2]);
    const pars = await page.evaluateHandle(div => div.querySelectorAll('div > p'), nodes[4]);

    // Hide paragraphs, get text
    const [split_sentences, para_sentences] = await page.evaluate((pars) => {
        const text = [];
        for (const p of pars) {
            text.push(p.textContent);
            p.style['display'] = 'none';
        }
        return split_paragraphs(text);
    }, pars);


    const rows = [{name: 'title', path: 'img/title.jpeg', text: title}];

    let sentence_index = 0;
    for (var i=0; i<para_sentences.length; ++i) {
        // Un-hide individual paragraphs
        await page.evaluate((pars, i) => { pars[i].style['display'] = 'block'; }, pars, i);

        for (const para_sentence of para_sentences[i]) {
            const path = `img/post_frame${sentence_index}.jpeg`;
            const text = split_sentences[sentence_index].trim();
            // Change the text of the current paragraph to add in the next sentence
            await page.evaluate((pars, i, para_sentence) => { pars[i].innerHTML = para_sentence }, pars, i, para_sentence);
            await titleDiv.screenshot({path, quality: 100});

            rows.push({name: `post_frame${sentence_index}`, path, text});
            ++sentence_index;
        }
    }

    const csvWriter = createCsvWriter({  
        path: 'text/9uhk57.csv',
        header: [{id: 'name', title: 'Name'}, {id: 'path', title: 'Path'}, {id: 'text', title: 'Text'}]
    });

    await csvWriter.writeRecords(rows);

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